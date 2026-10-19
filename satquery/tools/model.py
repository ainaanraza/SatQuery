from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence
from satquery.models.manager import ModelManager
from satquery.models.base import ModelInferenceRequest

class VisionAnswerTool(SatQueryTool):
    name = "vision.answer"
    description = "Sends the image and question to the SatQuery Vision-Language Model."
    capabilities = ToolCapabilities(vision=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        question = arguments.get("question", "")
        image = arguments.get("image")
        if image is None or not hasattr(image, "path"):
            return ToolResult(success=False, tool_name=self.name, errors=["vision.answer requires an input image."])

        provider = ModelManager.get_provider()
        req = ModelInferenceRequest(prompt=question, image_paths=[image.path])
        result = provider.infer(req)

        text = result.predictions.get("text") if isinstance(result.predictions, dict) else None
        if result.status != "success":
            return ToolResult(success=False, tool_name=self.name,
                              errors=[f"Model inference failed ({result.provider}): {text or result.status}"])
        if not text:
            return ToolResult(success=False, tool_name=self.name,
                              errors=[f"Model provider '{result.provider}' returned no answer text."])

        ev = Evidence(
            source_type="model_inference",
            source=image.path,
            tool=self.name,
            confidence=result.confidence,
            metadata={"provider": result.provider, "model_id": result.model_id}
        )
        return ToolResult(success=True, tool_name=self.name, data=text, evidence=[ev])
