import pytest
from satquery.tools.registry import ToolRegistry
from satquery.tools.raster import RasterInspectTool
from satquery.tools.change_detection import ChangeDetectionTool

def test_tool_registry():
    reg = ToolRegistry()
    tool = RasterInspectTool()
    reg.register(tool)
    assert reg.has("raster.inspect")
    assert reg.get("raster.inspect") == tool

def test_change_detection_percentage():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": 250,
            "valid_pixel_count": 1000,
        },
    )

    assert result.success
    assert result.data["change_percentage"] == 25.0


def test_change_detection_zero_changed_pixels():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": 0,
            "valid_pixel_count": 1000,
        },
    )

    assert result.success
    assert result.data["change_percentage"] == 0.0


def test_change_detection_all_pixels_changed():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": 1000,
            "valid_pixel_count": 1000,
        },
    )

    assert result.success
    assert result.data["change_percentage"] == 100.0


def test_change_detection_rejects_nonpositive_valid_pixel_count():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": 100,
            "valid_pixel_count": 0,
        },
    )

    assert not result.success
    assert "greater than 0" in result.errors[0]


def test_change_detection_rejects_negative_changed_pixel_count():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": -1,
            "valid_pixel_count": 1000,
        },
    )

    assert not result.success
    assert "must not be negative" in result.errors[0]


def test_change_detection_rejects_changed_count_above_valid_count():
    tool = ChangeDetectionTool()

    result = tool.execute(
        None,
        {
            "changed_pixel_count": 1001,
            "valid_pixel_count": 1000,
        },
    )

    assert not result.success
    assert "must not exceed" in result.errors[0]
