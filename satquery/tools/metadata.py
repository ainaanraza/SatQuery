from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.inputs.raster_loader import load_raster
from satquery.evidence.models import Evidence

class RasterMetadataTool(SatQueryTool):
    name = "raster.metadata"
    description = "Extracts metadata like sensor, modality, acquisition time"
    capabilities = ToolCapabilities(metadata=True)
    
    def execute(self, context, arguments: dict) -> ToolResult:
        path = arguments.get("path")
        if not path:
            return ToolResult(success=False, tool_name=self.name, errors=["No path provided"])
            
        try:
            img = load_raster(path)
            data = {
                "sensor": img.sensor,
                "modality": img.modality,
                "acquisition_time": img.acquisition_time,
                "geospatial_metadata": img.metadata
            }
            ev = Evidence(
                source_type="metadata",
                source=path,
                tool=self.name,
                confidence=1.0
            )
            return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, errors=[str(e)])
