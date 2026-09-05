import numpy as np
import rasterio

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence


class ChangeDetectionTool(SatQueryTool):
    name = "change_detection"
    description = "Detects differences between two spatially aligned images."
    capabilities = ToolCapabilities(raster=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        img_a = arguments.get("image_a")
        img_b = arguments.get("image_b")
        method = arguments.get("method", "absolute_difference")

        if not img_a or not img_b:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Two images required"]
            )

        if method != "absolute_difference":
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=[f"Unsupported change detection method: {method}"]
            )

        try:
            with rasterio.open(img_a.path) as src_a:
                raster_a = src_a.read(masked=True)

            with rasterio.open(img_b.path) as src_b:
                raster_b = src_b.read(masked=True)

            if raster_a.shape != raster_b.shape:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    errors=["Images must have the same dimensions and band count"]
                )

            mask_a = np.ma.getmaskarray(raster_a)
            mask_b = np.ma.getmaskarray(raster_b)

            # A pixel is valid only when it is valid in both images.
            valid_mask = ~(mask_a.any(axis=0) | mask_b.any(axis=0))

            difference = np.abs(
                raster_a.data.astype(np.float32)
                - raster_b.data.astype(np.float32)
            )

            # Only valid pixels can be considered changed.
            changed_mask = np.any(difference > 0, axis=0) & valid_mask

            changed_pixel_count = int(np.count_nonzero(changed_mask))
            valid_pixel_count = int(np.count_nonzero(valid_mask))

            change_percentage = (
                changed_pixel_count / valid_pixel_count * 100
                if valid_pixel_count > 0
                else 0.0
            )

            data = {
                "method": method,
                "changed_pixel_count": changed_pixel_count,
                "valid_pixel_count": valid_pixel_count,
                "change_percentage": change_percentage,
                "mask": changed_mask
            }

            ev = Evidence(
                source_type="raster_analysis",
                source=f"{img_a.path}, {img_b.path}",
                tool=self.name,
                metadata={
                    "method": method,
                    "changed_pixel_count": changed_pixel_count,
                    "valid_pixel_count": valid_pixel_count,
                    "change_percentage": change_percentage
                }
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data=data,
                evidence=[ev]
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=[str(e)]
            )