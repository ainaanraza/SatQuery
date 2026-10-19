import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.windows import from_bounds as window_from_bounds

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

DEFAULT_THRESHOLD = 0.15
DEFAULT_MAX_SIZE = 2048


def _overlap_bounds(img_a, img_b):
    a_minx, a_miny, a_maxx, a_maxy = img_a.bounds
    b_minx, b_miny, b_maxx, b_maxy = img_b.bounds
    bounds = (max(a_minx, b_minx), max(a_miny, b_miny), min(a_maxx, b_maxx), min(a_maxy, b_maxy))
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        return None
    return bounds


def _read_on_grid(image, bounds, band_count, shape):
    """Read the first `band_count` bands of `image` over `bounds`, resampled onto a common grid shape."""
    with rasterio.open(image.path) as src:
        window = window_from_bounds(*bounds, transform=src.transform)
        return src.read(
            list(range(1, band_count + 1)),
            window=window,
            out_shape=(band_count, shape[0], shape[1]),
            resampling=Resampling.average,
            masked=True,
        )


def measure_change(img_a, img_b, threshold=DEFAULT_THRESHOLD, max_size=DEFAULT_MAX_SIZE):
    """Pixel-level absolute-difference change detection over the overlap of two rasters.

    Each band's absolute difference is scaled by that band's joint 2nd-98th percentile
    span across both images, so the threshold is a fraction of the typical value range;
    the per-pixel score is the mean scaled difference across bands. The overlap is read on image_a's pixel grid, downsampled so neither
    side exceeds `max_size` pixels to bound memory use.
    """
    if img_a.crs != img_b.crs:
        raise ValueError(f"CRS mismatch ({img_a.crs} vs {img_b.crs}); reprojection is not supported yet.")
    bounds = _overlap_bounds(img_a, img_b)
    if bounds is None:
        raise ValueError("Images do not overlap spatially.")

    width = max(1, round((bounds[2] - bounds[0]) / abs(img_a.resolution_x)))
    height = max(1, round((bounds[3] - bounds[1]) / abs(img_a.resolution_y)))
    scale = max(width, height) / max_size
    downsample = max(1.0, scale)
    shape = (max(1, round(height / downsample)), max(1, round(width / downsample)))

    band_count = min(img_a.band_count, img_b.band_count)
    data_a = _read_on_grid(img_a, bounds, band_count, shape)
    data_b = _read_on_grid(img_b, bounds, band_count, shape)

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
        "downsample_factor": round(downsample, 3),
        "mask": mask,
        "transform": transform_from_bounds(*bounds, shape[1], shape[0]),
        "crs": img_a.crs,
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
