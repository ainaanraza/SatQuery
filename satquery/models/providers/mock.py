from satquery.models.base import MultimodalModelProvider, ModelInferenceResult

class MockProvider(MultimodalModelProvider):
    def infer(self, request) -> ModelInferenceResult:
        return ModelInferenceResult(
            status="success",
            provider="mock",
            model_id="satquery-mock",
            model_version="1.0",
            predictions={"category": "UNKNOWN_CHANGE"},
            confidence=0.5
        )
