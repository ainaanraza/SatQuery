from .base import SatQueryTool
from satquery.evidence.models import Evidence
from satquery.reasoning.engine import ReasoningEngine

class ReasoningTool(SatQueryTool):
    name = "reasoning"
    description = "Grounds claims using VLM reasoning."
    
    def __init__(self, provider):
        self.engine = ReasoningEngine(provider)
        
    def execute(self, inputs: list, *args, **kwargs):
        evidence = [i for i in inputs if isinstance(i, Evidence)]
        query = kwargs.get("query", "")
        result = self.engine.reason(query, evidence)
        return Evidence(
            id="reasoning-1",
            source="mock_model",
            tool=self.name,
            confidence=result.confidence,
            result={"answer": result.answer}
        )
