import numpy as np
import rasterio

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence
from satquery.multimodal.registration import DEFAULT_MAX_SIZE, common_grid, read_on_grid

DEFAULT_THRESHOLD = 0.15


def measure_change(img_a, img_b, threshold=DEFAULT_THRESHOLD, max_size=DEFAULT_MAX_SIZE):
    """Pixel-level absolute-difference change detection over the overlap of two rasters.

    Each band's absolute difference is scaled by that band's joint 2nd-98th percentile
    span across both images, so the threshold is a fraction of the typical value range;
    the per-pixel score is the mean scaled difference across bands. The overlap is read
    on image_a's pixel grid, downsampled so neither side exceeds `max_size` pixels to
    bound memory use.
    """
    grid = common_grid(img_a, img_b, max_size)
    bounds, shape = grid["bounds"], grid["shape"]

    band_count = min(img_a.band_count, img_b.band_count)
    bands = list(range(1, band_count + 1))
    data_a = read_on_grid(img_a, bounds, bands, shape)
    data_b = read_on_grid(img_b, bounds, bands, shape)

    valid = ~(np.ma.getmaskarray(data_a).any(axis=0) | np.ma.getmaskarray(data_b).any(axis=0))
    a = np.ma.getdata(data_a).astype(np.float32)
    b = np.ma.getdata(data_b).astype(np.float32)
    valid &= np.isfinite(a).all(axis=0) & np.isfinite(b).all(axis=0)
    valid_pixel_count = int(valid.sum())
    if valid_pixel_count == 0:
        raise ValueError("No valid (non-nodata) overlapping pixels to compare.")

    diff = np.zeros(shape, dtype=np.float32)
    for i in range(band_count):
        joint = np.concatenate([a[i][valid], b[i][valid]])
        p_low, p_high = np.percentile(joint, [2, 98])
        span = p_high - p_low
        if span <= 0:
            continue
        # The percentile span is only a robust scale; values are not clipped, since
        # genuine change often sits in the tails (e.g. new bright rooftops).
        diff += np.abs(a[i] - b[i]) / span
    diff /= band_count

    mask = (diff > threshold) & valid
    changed_pixel_count = int(mask.sum())

    return {
        "changed_pixel_count": changed_pixel_count,
        "valid_pixel_count": valid_pixel_count,
        "threshold": threshold,
        "bands_compared": band_count,
        "overlap_bounds": bounds,
        "grid_shape": shape,
        "downsample_factor": grid["downsample_factor"],
        "mask": mask,
        "transform": grid["transform"],
        "crs": grid["crs"],
    }


class ChangeDetectionTool(SatQueryTool):
    name = "change_detection"
    description = "Detects differences between two spatially aligned images."
    capabilities = ToolCapabilities(raster=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        method = arguments.get("method", "absolute_difference")
        img_a = arguments.get("image_a")
        img_b = arguments.get("image_b")
        warnings = []

        if img_a is not None and img_b is not None:
            if method != "absolute_difference":
                return ToolResult(success=False, tool_name=self.name, errors=[f"Unsupported change detection method: {method}"])
            try:
                measured = measure_change(
                    img_a,
                    img_b,
                    threshold=arguments.get("threshold", DEFAULT_THRESHOLD),
                    max_size=arguments.get("max_size", DEFAULT_MAX_SIZE),
                )
            except (ValueError, rasterio.errors.RasterioError) as e:
                return ToolResult(success=False, tool_name=self.name, errors=[f"Change detection failed: {e}"])
            if img_a.band_count != img_b.band_count:
                warnings.append(
                    f"Band counts differ ({img_a.band_count} vs {img_b.band_count}); "
                    f"compared the first {measured['bands_compared']} bands."
                )
            if measured["downsample_factor"] > 1:
                warnings.append(f"Overlap was downsampled by {measured['downsample_factor']}x for change detection.")
            changed_pixel_count = measured["changed_pixel_count"]
            valid_pixel_count = measured["valid_pixel_count"]
        elif "changed_pixel_count" in arguments and "valid_pixel_count" in arguments:
            # Pre-computed counts (e.g. from an external detector).
            measured = {}
            changed_pixel_count = arguments["changed_pixel_count"]
            valid_pixel_count = arguments["valid_pixel_count"]
        else:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Change detection requires image_a and image_b, or changed_pixel_count and valid_pixel_count."],
            )

        if valid_pixel_count <= 0:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["valid_pixel_count must be greater than 0"],
            )

        if changed_pixel_count < 0:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["changed_pixel_count must not be negative"],
            )

        if changed_pixel_count > valid_pixel_count:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["changed_pixel_count must not exceed valid_pixel_count"],
            )

        change_percentage = (changed_pixel_count / valid_pixel_count) * 100

        data = {
            **measured,
            "method": method,
            "changed_pixel_count": changed_pixel_count,
            "valid_pixel_count": valid_pixel_count,
            "change_percentage": round(change_percentage, 2),
        }

        # Evidence metadata stays JSON-serializable: the mask array and Affine are kept out.
        ev_meta = {k: v for k, v in data.items() if k not in ("mask", "transform", "crs")}
        transform = data.get("transform")
        ev = Evidence(
            source_type="raster_analysis",
            source=f"{img_a.path}, {img_b.path}" if img_a is not None and img_b is not None else "pixel_counts",
            tool=self.name,
            bounds=data.get("overlap_bounds"),
            crs=data.get("crs"),
            transform=list(transform)[:6] if transform is not None else None,
            metadata=ev_meta,
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
            evidence=[ev],
            warnings=warnings,
        )
