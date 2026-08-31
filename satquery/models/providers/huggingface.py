from satquery.models.base import MultimodalModelProvider, ModelInferenceResult

class HuggingFaceProvider(MultimodalModelProvider):
    def infer(self, request) -> ModelInferenceResult:
        return ModelInferenceResult(
            status="error",
            provider="huggingface",
            model_id="unknown",
            model_version="unknown",
            predictions={"error": "Not loaded"},
            confidence=0.0
        )
