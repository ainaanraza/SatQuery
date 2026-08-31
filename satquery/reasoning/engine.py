from .context import ContextBuilder
from .grounding import GroundingEngine
from .models import ReasoningResult

class ReasoningEngine:
    def __init__(self, provider):
        self.provider = provider
        self.context = ContextBuilder()
        self.grounding = GroundingEngine()
        
    def reason(self, query, evidence):
        ctx = self.context.build(query, evidence)
        raw_claims = ["The detected changed area is 14.2%."]
        claims = [self.grounding.evaluate(c, evidence) for c in raw_claims]
        
        return ReasoningResult(
            answer="Grounded answer based on evidence.",
            claims=claims,
            confidence=0.9,
            evidence_ids=[e.id for e in evidence],
            timeline=[],
            regions=[],
            warnings=[],
            model="mock_model",
            provider="mock"
        )
