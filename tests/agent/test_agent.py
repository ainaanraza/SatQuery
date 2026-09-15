import pytest
from satquery.agent.agent import SatQueryAgent
from satquery.inputs.models import RSImage
from satquery.evidence.models import Evidence

def mock_rsimage(path):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=None,
        crs="EPSG:4326",
        bounds=(0,0,10,10),
        transform=None,
        width=100,
        height=100,
        resolution_x=1,
        resolution_y=1,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )

def test_agent_vqa():
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("What is visible in this satellite image?", inputs=[img])
    assert "visible" in response.answer.lower() or "analyzed" in response.answer.lower()
    assert len(response.evidence) >= 1
    assert any("vision.answer" in ev.tool for ev in response.evidence)

def test_agent_metadata():
    agent = SatQueryAgent()
    img = mock_rsimage("test2.tif")
    response = agent.run("What sensor captured this image?", inputs=[img])
    assert "sensor" in response.answer.lower() or "mock_sensor" in response.answer.lower() or "dictionary" in str(type(response.answer)) or "mock_sensor" in str(response.answer)
    assert len(response.evidence) >= 1

def test_scene_description_classification():
    """Verify that scene description queries are classified as scene_description intent."""
    from satquery.agent.parser import QueryUnderstandingBackend
    backend = QueryUnderstandingBackend()
    scene_queries = [
        "Describe this image",
        "Describe the scene",
        "What is visible in this image?",
        "Give me a scene description",
        "Describe the land cover in this image",
    ]
    for q in scene_queries:
        parsed = backend.parse(q)
        assert parsed.operation == "scene_description", f"Expected 'scene_description' for query '{q}', got '{parsed.operation}'"

def test_scene_description_routing():
    """Verify that scene_description queries route through vision.answer with evidence."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])
    assert len(response.evidence) >= 1
    assert any("vision.answer" in ev.tool for ev in response.evidence)
    assert response.answer is not None

def test_scene_description_land_cover_query():
    """Verify realistic land cover query is classified as scene_description with image input."""
    from satquery.agent.parser import QueryUnderstandingBackend
    backend = QueryUnderstandingBackend()
    parsed = backend.parse("Describe the land cover and major objects visible in this satellite image")
    assert parsed.operation == "scene_description"
    assert "image" in parsed.required_inputs


def test_scene_description_trace():
    """A scene description request produces a trace with intent, tools, and evidence."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])

    assert response.trace is not None, "Response should contain an execution trace"

    # 1. Detected task or intent
    assert response.trace.detected_intent == "scene_description", (
        f"Expected 'scene_description', got '{response.trace.detected_intent}'"
    )
    assert response.trace.intent_confidence is not None, (
        "Trace should include intent confidence"
    )

    # 2 & 3. Tools selected and execution order
    assert "raster.preview" in response.trace.tools, (
        f"Trace should include 'raster.preview' in tools, got {response.trace.tools}"
    )
    assert "vision.answer" in response.trace.tools, (
        f"Trace should include 'vision.answer' in tools, got {response.trace.tools}"
    )
    assert response.trace.tools.index("raster.preview") < response.trace.tools.index("vision.answer"), (
        "raster.preview should execute before vision.answer"
    )

    # 4. Model used for inference
    assert response.trace.model_used is not None, (
        f"Trace should identify the model used, got model_used={response.trace.model_used}"
    )

    # 5. Relevant tool parameters
    assert len(response.trace.tool_parameters) == len(response.trace.tools), (
        "Each tool should have corresponding parameters"
    )
    vision_params = response.trace.tool_parameters[response.trace.tools.index("vision.answer")]
    assert "question" in vision_params, (
        f"vision.answer parameters should include 'question', got {vision_params}"
    )
    assert "image" in vision_params, (
        f"vision.answer parameters should include 'image', got {vision_params}"
    )

    # 6. Evidence produced
    assert len(response.trace.evidence) >= 1, (
        "Trace should contain at least one evidence item"
    )

    # 7. Confidence information
    assert response.trace.confidence is not None, (
        "Trace should include confidence information"
    )

    # 8. Errors or warnings
    assert isinstance(response.trace.errors, list), (
        "Trace errors should be a list"
    )
    assert isinstance(response.trace.warnings, list), (
        "Trace warnings should be a list"
    )


def test_missing_input_path_error_survives():
    """A missing input path produces a validation error that survives into the agent state/final response."""
    agent = SatQueryAgent()
    response = agent.run("What is in this image?", inputs=["nonexistent_file.tif"])
    # The validation error should be captured and appear in the answer
    assert response is not None
    assert "Failed due to errors" in response.answer
    assert any("does not exist" in err for err in [response.answer])


def test_unsupported_file_type_error_survives():
    """An unsupported file type produces a validation error that survives into the agent state/final response."""
    import tempfile
    import os
    agent = SatQueryAgent()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not a raster")
        path = f.name
    try:
        response = agent.run("What is in this image?", inputs=[path])
        assert response is not None
        assert "Failed due to errors" in response.answer
        assert any("Unsupported file type" in err for err in [response.answer])
    finally:
        os.unlink(path)


def test_valid_raster_still_resolves():
    """A valid raster still resolves successfully."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("What sensor captured this image?", inputs=[img])
    assert response is not None
    assert "Failed due to errors" not in response.answer
    assert len(response.evidence) >= 1


def test_response_with_evidence_is_supported():
    """A response that includes evidence is marked as supported."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])
    assert response.has_evidence is True
    assert response.evidence_count >= 1
    assert response.coverage_status == "supported"


def test_response_without_evidence_is_insufficient():
    """A response with no evidence is marked as insufficient_evidence."""
    from satquery.agent.synthesizer import SatQueryResponse
    response = SatQueryResponse(answer="No evidence available", evidence=[])
    assert response.has_evidence is False
    assert response.evidence_count == 0
    assert response.coverage_status == "insufficient_evidence"


def test_evidence_provenance_preserved():
    """Evidence provenance (source_type, tool, source, confidence) is exposed in the response."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])

    assert len(response.evidence_provenance) >= 1, (
        "Response should have at least one provenance entry"
    )

    for entry in response.evidence_provenance:
        assert "source_type" in entry, (
            f"Provenance entry missing 'source_type': {entry}"
        )
        assert "tool" in entry, (
            f"Provenance entry missing 'tool': {entry}"
        )
        assert "source" in entry, (
            f"Provenance entry missing 'source': {entry}"
        )
        assert "confidence" in entry, (
            f"Provenance entry missing 'confidence': {entry}"
        )


def test_scene_description_has_evidence():
    """A scene description response still contains evidence."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])

    assert len(response.evidence) >= 1, (
        "Scene description response should contain evidence"
    )
    assert any("vision.answer" in ev.tool for ev in response.evidence), (
        "Scene description should have vision.answer evidence"
    )


def test_coverage_fields_still_work():
    """Existing coverage fields (has_evidence, evidence_count, coverage_status) still work."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])

    assert response.has_evidence is True
    assert response.evidence_count >= 1
    assert response.coverage_status == "supported"


def test_trace_still_passes():
    """Existing execution trace tests still pass."""
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("Describe this image", inputs=[img])

    assert response.trace is not None
    assert response.trace.detected_intent == "scene_description"
    assert "raster.preview" in response.trace.tools
    assert "vision.answer" in response.trace.tools
    assert len(response.trace.evidence) >= 1
