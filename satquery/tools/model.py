from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class VisionAnswerTool(SatQueryTool):
    name = "vision.answer"
    description = "Sends the image and question to the SatQuery Vision-Language Model."
    capabilities = ToolCapabilities(vision=True)
    
    def execute(self, context, arguments: dict) -> ToolResult:
        # Mocking the real VLM integration for agent orchestration
        question = arguments.get("question")
        image = arguments.get("image")
        
        data = f"Mocked answer for: {question}"
        ev = Evidence(
            source_type="model_inference",
            source=image.path if image else "unknown",
            tool=self.name,
            confidence=0.85
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
