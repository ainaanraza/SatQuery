import numpy as np
from rasterio.transform import array_bounds

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence


class ChangeLocalizationTool(SatQueryTool):
    name = "change_localization"
    description = "Translates pixel-based change into geographic areas."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        mask = arguments.get("mask")
        pixel_area_sqm = arguments.get("pixel_area_sqm", 1)
        transform = arguments.get("transform")

        if mask is None:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Change mask required"]
            )

        changed_pixel_count = int(np.count_nonzero(mask))
        changed_area_sqm = changed_pixel_count * pixel_area_sqm

        overall_change_bounds = None

        if changed_pixel_count > 0 and transform is not None:
            rows, cols = np.where(mask)

            min_row = int(rows.min())
            max_row = int(rows.max())
            min_col = int(cols.min())
            max_col = int(cols.max())

            left, top = transform * (min_col, min_row)
            right, bottom = transform * (max_col + 1, max_row + 1)

            overall_change_bounds = (
                min(left, right),
                min(bottom, top),
                max(left, right),
                max(bottom, top)
            )

        data = {
            "changed_pixel_count": changed_pixel_count,
            "changed_area_sqm": changed_area_sqm,
            "overall_change_bounds": overall_change_bounds
        }

        ev = Evidence(
            source_type="spatial_analysis",
            source="change_mask",
            tool=self.name,
            metadata=data
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
            evidence=[ev]
        )