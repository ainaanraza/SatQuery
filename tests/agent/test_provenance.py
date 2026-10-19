import json
from datetime import datetime

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from satquery.agent.agent import SatQueryAgent
from satquery.jobs.manager import JobManager
from satquery.visualization.serialization import to_jsonable


def write_raster(path, data, tags=None):
    with rasterio.open(
        path, "w", driver="GTiff", height=data.shape[1], width=data.shape[2], count=data.shape[0],
        dtype=data.dtype, crs="EPSG:32643", transform=from_origin(500000.0, 1400000.0, 10.0, 10.0),
    ) as dst:
        dst.write(data)
        if tags:
            dst.update_tags(**tags)
    return str(path)


@pytest.fixture
def change_pair(tmp_path):
    before = np.random.default_rng(0).integers(0, 100, size=(3, 64, 64), dtype=np.uint8)
    after = before.copy()
    after[:, 10:20, 10:20] = 255
    return (write_raster(tmp_path / "before.tif", before, {"ACQUISITION_DATE": "2021-01-01"}),
            write_raster(tmp_path / "after.tif", after, {"ACQUISITION_DATE": "2022-01-01"}))


def edges_by_tool(graph):
    """Edges as (source label, target label), labelling steps by tool name and inputs by path."""
    labels = {}
    for node in graph["nodes"]:
        if node["type"] == "tool":
            labels[node["id"]] = node["data"]["tool"]
        elif node["type"] == "input":
            labels[node["id"]] = node["data"]["path"].replace("\\", "/").split("/")[-1]
        else:
            labels[node["id"]] = node["id"]
    return {(labels[e["source"]], labels[e["target"]]) for e in graph["edges"]}


def test_change_analysis_graph_reflects_data_flow(change_pair):
    response = SatQueryAgent().run("What changed between the images?", inputs=list(change_pair))
    edges = edges_by_tool(response.evidence_graph)

    for image in ("before.tif", "after.tif"):
        for tool in ("temporal_alignment", "spatial_alignment", "change_detection"):
            assert (image, tool) in edges
    assert ("change_detection", "change_localization") in edges
    assert ("change_detection", "change_summary") in edges
    assert ("change_localization", "change_summary") in edges
    assert ("temporal_alignment", "change_summary") in edges
    assert ("change_summary", "answer") in edges
    # Inputs feed only the steps that actually take images.
    assert ("before.tif", "change_summary") not in edges
    assert response.answer_source == "change_summary"


def test_failed_run_links_failing_step_to_answer(tmp_path):
    a = write_raster(tmp_path / "a.tif", np.zeros((3, 10, 10), dtype=np.uint8))
    with rasterio.open(
        tmp_path / "far.tif", "w", driver="GTiff", height=10, width=10, count=3, dtype="uint8",
        crs="EPSG:32643", transform=from_origin(900000.0, 1400000.0, 10.0, 10.0),
    ) as dst:
        dst.write(np.zeros((3, 10, 10), dtype=np.uint8))

    response = SatQueryAgent().run("Detect change before and after", inputs=[a, str(tmp_path / "far.tif")])
    edges = edges_by_tool(response.evidence_graph)

    assert not response.success
    assert ("spatial_alignment", "answer") in edges
    assert not any(node["data"].get("tool") == "change_detection" for node in response.evidence_graph["nodes"])


def test_vqa_graph_links_vision_answer():
    response = SatQueryAgent().run("What is visible in this image?", inputs=["test1.tif"])
    edges = edges_by_tool(response.evidence_graph)

    assert ("test1.tif", "vision.answer") in edges
    assert ("vision.answer", "answer") in edges


def test_job_result_is_strict_json(change_pair):
    jobs = JobManager()
    job_id = jobs.submit({"query": "What changed between before and after?", "inputs": list(change_pair)})
    jobs.execute_sync(job_id)
    job = jobs.get_status(job_id)

    assert job["status"] == "completed"
    result = json.loads(json.dumps(job["result"]))  # raises if anything is not plain JSON
    assert result["success"] is True
    assert result["confidence"] is None  # purely deterministic measurement
    assert result["evidence_graph"]["edges"]
    temporal = next(n for n in result["evidence_graph"]["nodes"] if n["data"].get("tool") == "temporal_alignment")
    assert temporal["data"]["evidence"][0]["metadata"]["before_time"] == "2021-01-01T00:00:00"


def test_to_jsonable_handles_agent_types():
    from affine import Affine
    value = {"t": datetime(2020, 1, 2), "a": np.zeros((2, 3)), "n": np.float32(1.5), "tr": Affine(10, 0, 5, 0, -10, 7), "tup": (1, 2)}
    assert to_jsonable(value) == {
        "t": "2020-01-02T00:00:00", "a": {"array_shape": [2, 3], "dtype": "float64"}, "n": 1.5,
        "tr": [10.0, 0.0, 5.0, 0.0, -10.0, 7.0], "tup": [1, 2],
    }
