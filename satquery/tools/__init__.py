from .registry import ToolRegistry
from .raster import RasterInspectTool, RasterTileTool
from .metadata import RasterMetadataTool
from .preview import PreviewTool
from .model import VisionAnswerTool

def get_default_registry():
    reg = ToolRegistry()
    reg.register(RasterInspectTool())
    reg.register(RasterTileTool())
    reg.register(RasterMetadataTool())
    reg.register(PreviewTool())
    reg.register(VisionAnswerTool())
    return reg
