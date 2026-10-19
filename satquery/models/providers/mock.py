from satquery.models.base import MultimodalModelProvider, ModelInferenceResult

class MockProvider(MultimodalModelProvider):
    """Placeholder provider for development and tests; it never looks at the image."""

    def infer(self, request) -> ModelInferenceResult:
        return ModelInferenceResult(
            status="success",
            provider="mock",
            model_id="satquery-mock",
            model_version="1.0",
            predictions={
                "text": f"[mock provider - no vision model loaded] Analyzed question: {request.prompt}",
                "category": "UNKNOWN_CHANGE",
            },
            confidence=0.5,
            input_sources=list(request.image_paths),
        )
