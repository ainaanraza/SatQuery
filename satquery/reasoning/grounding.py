from .models import ReasoningClaim

class GroundingEngine:
    def evaluate(self, claim: str, evidence) -> ReasoningClaim:
        return ReasoningClaim(
            claim_id="C1",
            text=claim,
            confidence=0.9,
            status="SUPPORTED" if evidence else "UNSUPPORTED",
            evidence_ids=[e.id for e in evidence],
            source_type="mock/model_inference"
        )
