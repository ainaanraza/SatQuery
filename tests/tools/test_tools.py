import pytest
from satquery.tools.registry import ToolRegistry
from satquery.tools.raster import RasterInspectTool

def test_tool_registry():
    reg = ToolRegistry()
    tool = RasterInspectTool()
    reg.register(tool)
    assert reg.has("raster.inspect")
    assert reg.get("raster.inspect") == tool
