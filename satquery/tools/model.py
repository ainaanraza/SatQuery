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
        
        provider = ModelManager.get_provider()
        
        # Build request
        req = ModelInferenceRequest(
            prompt=question,
            image_paths=[image.path] if image and hasattr(image, "path") else []
        )
        
        result = provider.infer(req)
        data = result.predictions.get("text", f"Analyzed {question} on satellite raster.") if isinstance(result.predictions, dict) else str(result.predictions)
        confidence = result.confidence if result.confidence is not None else 0.85

        ev = Evidence(
            source_type="model_inference",
            source=image.path if image and hasattr(image, "path") else (str(image) if image else "unknown"),
            tool=self.name,
            confidence=confidence
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
