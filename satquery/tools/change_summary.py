from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class ChangeSummaryTool(SatQueryTool):
    name = "change_summary"
    description = "Translates numerical change data into structured analytical summaries."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        stats = arguments.get("statistics") or {}
        localization = arguments.get("localization") or {}
        temporal = arguments.get("temporal") or {}

        if "change_percentage" not in stats:
            return ToolResult(success=False, tool_name=self.name, errors=["No change statistics provided."])

        pct = stats["change_percentage"]
        parts = [f"Measured change: {pct}% of valid pixels exceeded the configured threshold"]
        if "valid_pixel_count" in stats:
            parts[0] += f" ({stats['changed_pixel_count']:,} of {stats['valid_pixel_count']:,} overlapping pixels"
            if "threshold" in stats:
                parts[0] += f", threshold {stats['threshold']} on scaled absolute difference"
            parts[0] += ")"
        parts[0] += "."

        if localization.get("changed_area_sqm"):
            area = localization["changed_area_sqm"]
            regions = localization.get("region_count", 0)
            parts.append(f"Changed area is approximately {area:,.0f} m² across {regions} region(s).")
            if localization.get("regions"):
                largest = localization["regions"][0]
                bounds = ", ".join(f"{v:.6g}" for v in largest["bounds"])
                parts.append(f"Largest region: {largest['area_sqm']:,.0f} m² at bounds ({bounds}).")

        order = temporal.get("temporal_order")
        if order == "before_after":
            parts.append(f"Acquisition order: {temporal['before_time']} -> {temporal['after_time']}.")
        elif order == "simultaneous":
            parts.append("Both images report the same acquisition time.")
        elif order == "unknown":
            parts.append("Acquisition order is unknown (no capture dates in the image metadata).")

        data = {
            "summary": " ".join(parts),
            "interpretation": "The system cannot determine the cause of change from pixel differences alone."
        }

        ev = Evidence(
            source_type="synthesis",
            source="change_stats",
            tool=self.name,
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
