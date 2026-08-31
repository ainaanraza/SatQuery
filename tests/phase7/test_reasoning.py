import pytest
from satquery.reasoning.engine import ReasoningEngine
from satquery.evidence.models import Evidence

def test_grounding():
    engine = ReasoningEngine(provider="mock")
    ev = Evidence(id="E1", source="img", tool="test", confidence=0.9, result={})
    res = engine.reason("What changed?", [ev])
    assert res.claims[0].status == "SUPPORTED"
