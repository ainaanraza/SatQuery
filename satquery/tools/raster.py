from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.inputs.raster_loader import load_raster
from satquery.evidence.models import Evidence
from satquery.inputs.tiling import iter_tiles

class RasterInspectTool(SatQueryTool):
    name = "raster.inspect"
    description = "Inspects raster file and returns properties"
    capabilities = ToolCapabilities(raster=True)
    
    def execute(self, context, arguments: dict) -> ToolResult:
        path = arguments.get("path")
        if not path:
            return ToolResult(success=False, tool_name=self.name, errors=["No path provided"])
            
        try:
            img = load_raster(path)
            data = {
                "dimensions": (img.width, img.height),
                "bands": img.band_count,
                "crs": img.crs,
                "bounds": img.bounds,
                "resolution": (img.resolution_x, img.resolution_y),
                "nodata": img.nodata,
                "dtype": img.dtype
            }
            ev = Evidence(
                source_type="raster",
                source=path,
                tool=self.name,
                bounds=img.bounds,
                crs=img.crs,
                transform=img.transform
            )
            return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, errors=[str(e)])

class RasterTileTool(SatQueryTool):
    name = "raster.tile"
    description = "Extracts tiles from a raster image."
    capabilities = ToolCapabilities(raster=True)
    
    def execute(self, context, arguments: dict) -> ToolResult:
        image = arguments.get("image")
        tile_size = arguments.get("tile_size", 512)
        overlap = arguments.get("overlap", 0)
        
        try:
            tiles = list(iter_tiles(image, tile_size=tile_size, overlap=overlap))
            ev = Evidence(
                source_type="raster_tiles",
                source=image.path,
                tool=self.name,
                bounds=image.bounds,
                crs=image.crs
            )
            return ToolResult(success=True, tool_name=self.name, data=tiles, evidence=[ev])
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, errors=[str(e)])
