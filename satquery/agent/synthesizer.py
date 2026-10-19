from dataclasses import dataclass, field
from typing import List, Optional
from satquery.evidence.models import Evidence
from .state import AgentState

@dataclass
class SatQueryResponse:
    answer: str
    evidence: List[Evidence] = field(default_factory=list)
    confidence: Optional[float] = None
    limitations: List[str] = field(default_factory=list)

class Synthesizer:
    def synthesize(self, state: AgentState) -> SatQueryResponse:
        answer = "I could not generate an answer."
        limitations = []

        if state.errors:
            answer = "Failed due to errors: " + "; ".join(state.errors)
        else:
            vision_results = [r for r in state.results if r.tool_name == "vision.answer"]
            change_results = [r for r in state.results if r.tool_name == "change_summary"]
            fusion_results = [r for r in state.results if r.tool_name == "optical_sar_fusion"]
            metadata_results = [r for r in state.results if r.tool_name == "raster.metadata"]

            if vision_results:
                answer = vision_results[-1].data
            elif change_results:
                data = change_results[-1].data
                answer = data["summary"]
                limitations.append(data["interpretation"])
            elif fusion_results:
                data = fusion_results[-1].data
                answer = (f"Optical ({data['optical_source']}) and SAR ({data['sar_source']}) inputs were paired, "
                          "but quantitative optical-SAR fusion analysis is not implemented yet.")
            elif metadata_results:
                answer = str(metadata_results[-1].data)
            else:
                answer = "Execution completed, but no relevant tool provided a synthesis output."

        limitations.extend(state.warnings)
        if not state.evidence:
            limitations.append("I cannot reliably determine this from the available imagery.")

        # Only model-derived evidence carries a confidence; deterministic measurements don't.
        # Report the weakest link, or None when nothing probabilistic contributed.
        confidences = [ev.confidence for ev in state.evidence if ev.confidence is not None]
        confidence = min(confidences) if confidences and not state.errors else None

        return SatQueryResponse(
            answer=answer,
            evidence=state.evidence,
            confidence=confidence,
            limitations=limitations
        )
