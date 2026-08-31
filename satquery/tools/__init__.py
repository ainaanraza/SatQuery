from .registry import ToolRegistry
from .raster import RasterInspectTool, RasterTileTool
from .metadata import RasterMetadataTool
from .preview import PreviewTool
from .model import VisionAnswerTool
from .temporal_alignment import TemporalAlignmentTool
from .spatial_alignment import SpatialAlignmentTool
from .change_detection import ChangeDetectionTool
from .change_localization import ChangeLocalizationTool
from .optical_sar_fusion import OpticalSARFusionTool
from .change_summary import ChangeSummaryTool

def get_default_registry():
    reg = ToolRegistry()
    reg.register(RasterInspectTool())
    reg.register(RasterTileTool())
    reg.register(RasterMetadataTool())
    reg.register(PreviewTool())
    reg.register(VisionAnswerTool())
    reg.register(TemporalAlignmentTool())
    reg.register(SpatialAlignmentTool())
    reg.register(ChangeDetectionTool())
    reg.register(ChangeLocalizationTool())
    reg.register(OpticalSARFusionTool())
    reg.register(ChangeSummaryTool())
    return reg
