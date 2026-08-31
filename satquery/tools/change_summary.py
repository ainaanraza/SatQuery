from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class ChangeSummaryTool(SatQueryTool):
    name = "change_summary"
    description = "Translates numerical change data into structured analytical summaries."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        stats = arguments.get("statistics", {})
        pct = stats.get("change_percentage", 0)
        
        summary = f"Measured change: {pct}% of valid pixels exceeded the configured threshold."
        
        data = {
            "summary": summary,
            "interpretation": "The system cannot determine the cause of change from pixel differences alone."
        }
        
        ev = Evidence(
            source_type="synthesis",
            source="change_stats",
            tool=self.name,
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
