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
            
        return SatQueryResponse(
            answer=answer,
            evidence=state.evidence,
            confidence=0.9,
            limitations=limitations
        )
