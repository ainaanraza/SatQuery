from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence
from satquery.inputs.metadata import FALLBACK_TAGS

class TemporalAlignmentTool(SatQueryTool):
    name = "temporal_alignment"
    description = "Determines whether two images can be ordered temporally."
    capabilities = ToolCapabilities(temporal=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        img_a = arguments.get("image_a")
        img_b = arguments.get("image_b")
        if not img_a or not img_b:
            return ToolResult(success=False, tool_name=self.name, errors=["Two images required"])

        time_a = img_a.acquisition_time
        time_b = img_b.acquisition_time
        warnings = []

        if time_a and time_b:
            if time_a < time_b:
                order = "before_after"
                before = img_a
                after = img_b
            elif time_b < time_a:
                order = "before_after"
                before = img_b
                after = img_a
                warnings.append(
                    f"Inputs were given in reverse chronological order; {img_b.path} ({time_b}) "
                    f"is treated as the earlier image."
                )
            else:
                order = "simultaneous"
                before = img_a
                after = img_b
        else:
            order = "unknown"
            before = img_a
            after = img_b

        for img in (img_a, img_b):
            source = getattr(img, "acquisition_time_source", None)
            if source in FALLBACK_TAGS:
                warnings.append(f"Acquisition time of {img.path} comes from {source}, which may be the file's processing time.")
            elif source == "filename":
                warnings.append(f"Acquisition time of {img.path} was inferred from its filename.")

        data = {
            "before_time": before.acquisition_time if before.acquisition_time else "unknown",
            "after_time": after.acquisition_time if after.acquisition_time else "unknown",
            "before_path": before.path,
            "after_path": after.path,
            "temporal_order": order
        }

        ev = Evidence(
            source_type="metadata",
            source=f"{img_a.path}, {img_b.path}",
            tool=self.name,
            metadata=data
        )

        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev], warnings=warnings)
