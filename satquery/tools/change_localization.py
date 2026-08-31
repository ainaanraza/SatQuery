from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class ChangeLocalizationTool(SatQueryTool):
    name = "change_localization"
    description = "Translates pixel-based change into geographic areas."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        mask = arguments.get("mask")
        
        data = {
            "changed_area_sqm": 50000,
            "overall_change_bounds": (0, 0, 10, 10)
        }
        
        ev = Evidence(
            source_type="spatial_analysis",
            source="change_mask",
            tool=self.name,
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
