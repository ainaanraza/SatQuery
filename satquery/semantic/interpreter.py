from .models import SemanticChange
import uuid

class SemanticChangeInterpreter:
    def interpret(self, measurements, model_inferences=None):
        if not model_inferences:
            return SemanticChange(
                semantic_id=str(uuid.uuid4()),
                category="UNKNOWN_CHANGE",
                confidence=1.0,
                status="OBSERVED_CHANGE_ONLY",
                source_evidence="measurements"
            )
        # Apply mock semantic rules if model_inferences provided
        cat = model_inferences.get("category", "UNKNOWN_CHANGE")
        conf = model_inferences.get("confidence", 0.0)
        return SemanticChange(
            semantic_id=str(uuid.uuid4()),
            category=cat,
            confidence=conf,
            status="MODEL_INFERRED",
            source_evidence="model"
        )
