from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.inputs.preview import generate_preview
from satquery.evidence.models import Evidence

class PreviewTool(SatQueryTool):
    name = "raster.preview"
    description = "Generates a normalized UI preview of the raster."
    capabilities = ToolCapabilities(raster=True)
    
    def execute(self, context, arguments: dict) -> ToolResult:
        image = arguments.get("image")
        try:
            prev = generate_preview(image)
            ev = Evidence(
                source_type="preview",
                source=image.path,
                tool=self.name
            )
            return ToolResult(success=True, tool_name=self.name, data=prev, evidence=[ev])
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, errors=[str(e)])
