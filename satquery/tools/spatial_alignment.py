from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class SpatialAlignmentTool(SatQueryTool):
    name = "spatial_alignment"
    description = "Checks CRS, resolution, and overlap compatibility."
    capabilities = ToolCapabilities(metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        img_a = arguments.get("image_a")
        img_b = arguments.get("image_b")
        if not img_a or not img_b:
            return ToolResult(success=False, tool_name=self.name, errors=["Two images required"])

        same_crs = (img_a.crs == img_b.crs)
        same_resolution = (img_a.resolution_x == img_b.resolution_x and img_a.resolution_y == img_b.resolution_y)
        grid_aligned = img_a.transform == img_b.transform
        
        # Simple overlap check
        a_minx, a_miny, a_maxx, a_maxy = img_a.bounds
        b_minx, b_miny, b_maxx, b_maxy = img_b.bounds
        
        overlap_x = (a_minx < b_maxx and a_maxx > b_minx)
        overlap_y = (a_miny < b_maxy and a_maxy > b_miny)
        overlap = overlap_x and overlap_y

        compatible = same_crs and same_resolution and grid_aligned and overlap
        
        data = {
            "same_crs": same_crs,
            "same_resolution": same_resolution,
            "grid_aligned": grid_aligned,
            "overlap": overlap,
            "compatible": compatible
        }
        
        ev = Evidence(
            source_type="metadata",
            source=f"{img_a.path}, {img_b.path}",
            tool=self.name,
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
