from satquery.evidence.graph import EvidenceGraph, EvidenceNode
from satquery.inputs.models import RSImage
from satquery.visualization.serialization import to_jsonable
from .state import AgentState, ResultRef

INPUT_FIELDS = ("path", "modality", "sensor", "crs", "bounds", "width", "height", "band_count",
                "acquisition_time", "acquisition_time_source")


def _argument_sources(arguments):
    """Yield (RSImage inputs, ResultRef tool names) referenced by a tool call's arguments."""
    images, refs = [], []
    values = list(arguments.values())
    while values:
        value = values.pop()
        if isinstance(value, RSImage):
            images.append(value)
        elif isinstance(value, ResultRef):
            refs.append(value.tool_name)
        elif isinstance(value, dict):
            values.extend(value.values())
    return images, refs


def build_evidence_graph(state: AgentState, response) -> EvidenceGraph:
    """Provenance graph of one agent run: inputs -> tool steps -> answer.

    Edges come from the plan itself: an RSImage argument links that input to the step,
    a ResultRef links the referenced earlier step. The answer is linked from the step
    the synthesizer answered from (or the failing step).
    """
    graph = EvidenceGraph()

    input_ids = {}
    for i, image in enumerate(state.inputs):
        node_id = f"input:{i}"
        input_ids[id(image)] = node_id
        graph.add_node(EvidenceNode(node_id, "input", to_jsonable({f: getattr(image, f, None) for f in INPUT_FIELDS})))

    # Executor results line up with the plan prefix it actually ran.
    last_step_for_tool = {}
    for i, (call, result) in enumerate(zip(state.plan, state.results)):
        node_id = f"step:{i}"
        graph.add_node(EvidenceNode(node_id, "tool", to_jsonable({
            "tool": call.tool_name,
            "success": result.success,
            "errors": result.errors,
            "warnings": result.warnings,
            "evidence": result.evidence,
        })))
        images, refs = _argument_sources(call.arguments)
        for image in images:
            if id(image) in input_ids:
                graph.link(input_ids[id(image)], node_id)
        for tool_name in refs:
            if tool_name in last_step_for_tool:
                graph.link(last_step_for_tool[tool_name], node_id)
        last_step_for_tool[call.tool_name] = node_id

    graph.add_node(EvidenceNode("answer", "answer", to_jsonable({
        "answer": response.answer,
        "confidence": response.confidence,
        "source_tool": response.answer_source,
        "errors": response.errors,
    })))
    if response.answer_source in last_step_for_tool:
        graph.link(last_step_for_tool[response.answer_source], "answer")
    elif state.results and not state.results[-1].success:
        graph.link(f"step:{len(state.results) - 1}", "answer")
    return graph
