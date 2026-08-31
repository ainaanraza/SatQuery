import pytest
from satquery.multimodal.fusion import fuse_deterministic
from satquery.semantic.interpreter import SemanticChangeInterpreter
from satquery.confidence.scoring import ConfidenceScorer

def test_deterministic_fusion():
    op_rep = {"source": "opt.tif"}
    sar_rep = {"source": "sar.tif"}
    res = fuse_deterministic(op_rep, sar_rep)
    assert res.fusion_method == "deterministic_feature_stack"
    assert res.provenance_optical == "opt.tif"

def test_no_fake_semantics():
    interpreter = SemanticChangeInterpreter()
    res = interpreter.interpret({"change": 15})
    assert res.category == "UNKNOWN_CHANGE"
    assert res.status == "OBSERVED_CHANGE_ONLY"

def test_mock_semantic_model():
    interpreter = SemanticChangeInterpreter()
    res = interpreter.interpret({"change": 15}, model_inferences={"category": "CONSTRUCTION", "confidence": 0.90})
    assert res.category == "CONSTRUCTION"
    assert res.status == "MODEL_INFERRED"

def test_confidence():
    scorer = ConfidenceScorer()
    assert scorer.score(3, 0.9) == "HIGH_CONFIDENCE"
    assert scorer.score(1, 0.0) == "MEDIUM_CONFIDENCE"
