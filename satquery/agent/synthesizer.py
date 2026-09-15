from dataclasses import dataclass, field
from typing import List, Optional
from satquery.evidence.models import Evidence
from .state import AgentState
from .trace import ExecutionTrace

@dataclass
class SatQueryResponse:
    answer: str
    evidence: List[Evidence] = field(default_factory=list)
    confidence: Optional[float] = None
    limitations: List[str] = field(default_factory=list)
    trace: Optional[ExecutionTrace] = None
    has_evidence: bool = False
    evidence_count: int = 0
    coverage_status: str = "insufficient_evidence"

class Synthesizer:
    def synthesize(self, state: AgentState) -> SatQueryResponse:
        answer = "I could not generate an answer."
        limitations = []

        if state.errors:
            answer = "Failed due to errors: " + "; ".join(state.errors)
        else:
            # Check results from vision.answer or metadata tools
            vision_results = [r for r in state.results if r.tool_name == "vision.answer"]
            metadata_results = [r for r in state.results if r.tool_name == "raster.metadata"]

            if vision_results:
                answer = vision_results[-1].data
            elif metadata_results:
                answer = str(metadata_results[-1].data)
            else:
                answer = "Execution completed, but no relevant tool provided a synthesis output."

        if not state.evidence:
            limitations.append("I cannot reliably determine this from the available imagery.")

        trace = self._build_trace(state)
        evidence_count = len(state.evidence)

        return SatQueryResponse(
            answer=answer,
            evidence=state.evidence,
            confidence=0.9,
            limitations=limitations,
            trace=trace,
            has_evidence=evidence_count > 0,
            evidence_count=evidence_count,
            coverage_status="supported" if evidence_count > 0 else "insufficient_evidence"
        )

    def _build_trace(self, state: AgentState) -> ExecutionTrace:
        model_used = None
        model_version = None
        model_confidence = None
        for result in state.results:
            if result.metadata and "model_id" in result.metadata:
                model_used = result.metadata.get("model_id")
                model_version = result.metadata.get("model_version")
                model_confidence = result.metadata.get("model_confidence")

        return ExecutionTrace(
            detected_intent=state.intent.name if state.intent else None,
            intent_confidence=state.intent.confidence if state.intent else None,
            tools=[call.tool_name for call in state.plan],
            tool_parameters=[call.arguments for call in state.plan],
            model_used=model_used,
            model_version=model_version,
            evidence=state.evidence,
            confidence=model_confidence if model_confidence is not None else (state.intent.confidence if state.intent else None),
            errors=list(state.errors),
            warnings=list(state.warnings),
        )
