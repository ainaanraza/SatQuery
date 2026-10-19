import math
from collections import deque

import numpy as np
from rasterio.crs import CRS

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

MAX_CELLS_PER_SIDE = 64
MIN_CELL_FRACTION = 0.1
MAX_REGIONS = 10


def _pixel_area_sqm(transform, crs, center_lat):
    """Approximate ground area of one pixel in square metres."""
    px_w, px_h = abs(transform.a), abs(transform.e)
    crs_obj = CRS.from_user_input(crs) if crs else None
    if crs_obj is not None and crs_obj.is_geographic:
        # Equirectangular approximation, adequate for scene-sized extents.
        metres_per_deg_lat = 110_574.0
        metres_per_deg_lon = 111_320.0 * math.cos(math.radians(center_lat))
        return px_w * metres_per_deg_lon * px_h * metres_per_deg_lat, "geographic_approximation"
    if crs_obj is not None and crs_obj.is_projected:
        factor = crs_obj.linear_units_factor[1] if crs_obj.linear_units_factor else 1.0
        return px_w * px_h * factor * factor, "projected"
    return None, "unknown_crs"


def _label_cells(cells):
    """4-connected component labelling of a small boolean grid (BFS; avoids a scipy dependency)."""
    labels = np.zeros(cells.shape, dtype=np.int32)
    current = 0
    for r, c in zip(*np.nonzero(cells)):
        if labels[r, c]:
            continue
        current += 1
        labels[r, c] = current
        queue = deque([(r, c)])
        while queue:
            y, x = queue.popleft()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < cells.shape[0] and 0 <= nx < cells.shape[1] and cells[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = current
                    queue.append((ny, nx))
    return labels, current


def _pixel_to_geo(transform, col, row):
    return (transform.c + col * transform.a + row * transform.b,
            transform.f + col * transform.d + row * transform.e)


def _pixel_bounds_to_geo(transform, row_min, row_max, col_min, col_max):
    x0, y0 = _pixel_to_geo(transform, col_min, row_min)
    x1, y1 = _pixel_to_geo(transform, col_max + 1, row_max + 1)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def localize_change(mask, transform, crs, max_regions=MAX_REGIONS):
    """Group changed pixels into regions and report their geographic bounds and areas.

    The mask is aggregated into a coarse cell grid (at most MAX_CELLS_PER_SIDE per side);
    cells with at least MIN_CELL_FRACTION changed pixels are connected into regions, and
    each region's bounds are then tightened to the changed pixels it contains.
    """
    height, width = mask.shape
    changed_total = int(mask.sum())

    center_y = _pixel_to_geo(transform, 0, height / 2)[1]
    pixel_area, area_method = _pixel_area_sqm(transform, crs, center_y)

    data = {
        "changed_pixel_count": changed_total,
        "changed_area_sqm": round(changed_total * pixel_area, 1) if pixel_area is not None else None,
        "area_method": area_method,
        "overall_change_bounds": None,
        "region_count": 0,
        "regions": [],
    }
    if changed_total == 0:
        return data

    rows, cols = np.nonzero(mask)
    data["overall_change_bounds"] = _pixel_bounds_to_geo(transform, rows.min(), rows.max(), cols.min(), cols.max())

    cell = max(1, math.ceil(max(height, width) / MAX_CELLS_PER_SIDE))
    grid_h, grid_w = math.ceil(height / cell), math.ceil(width / cell)
    padded = np.zeros((grid_h * cell, grid_w * cell), dtype=np.float32)
    padded[:height, :width] = mask
    fractions = padded.reshape(grid_h, cell, grid_w, cell).mean(axis=(1, 3))
    labels, count = _label_cells(fractions >= MIN_CELL_FRACTION)

    regions = []
    for label in range(1, count + 1):
        region_cells = np.kron(labels == label, np.ones((cell, cell), dtype=bool))[:height, :width]
        r, c = np.nonzero(mask & region_cells)
        if r.size == 0:
            continue
        regions.append({
            "bounds": _pixel_bounds_to_geo(transform, r.min(), r.max(), c.min(), c.max()),
            "pixel_count": int(r.size),
            "area_sqm": round(r.size * pixel_area, 1) if pixel_area is not None else None,
        })
    regions.sort(key=lambda reg: reg["pixel_count"], reverse=True)

    data["region_count"] = len(regions)
    data["regions"] = regions[:max_regions]
    return data


class ChangeLocalizationTool(SatQueryTool):
    name = "change_localization"
    description = "Translates pixel-based change into geographic areas."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        mask = arguments.get("mask")
        transform = arguments.get("transform")
        crs = arguments.get("crs")

        if not isinstance(mask, np.ndarray) or mask.ndim != 2:
            return ToolResult(success=False, tool_name=self.name, errors=["A 2-D change mask array is required."])
        if transform is None:
            return ToolResult(success=False, tool_name=self.name, errors=["The change mask's geotransform is required."])

        data = localize_change(mask.astype(bool), transform, crs, arguments.get("max_regions", MAX_REGIONS))

        warnings = []
        if data["area_method"] == "unknown_crs":
            warnings.append("CRS unknown; changed area could not be expressed in square metres.")
        if data["region_count"] > len(data["regions"]):
            warnings.append(f"Reporting the {len(data['regions'])} largest of {data['region_count']} change regions.")

        ev = Evidence(
            source_type="spatial_analysis",
            source="change_mask",
            tool=self.name,
            bounds=data["overall_change_bounds"],
            crs=crs,
            transform=list(transform)[:6],
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev], warnings=warnings)
