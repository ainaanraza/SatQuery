import pytest
from satquery.tools.temporal_alignment import TemporalAlignmentTool
from satquery.tools.spatial_alignment import SpatialAlignmentTool
from satquery.inputs.models import RSImage

def mock_rsimage(path, acq_time=None, crs="EPSG:4326", bounds=(0,0,10,10), res_x=1, res_y=1):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=acq_time,
        crs=crs,
        bounds=bounds,
        transform=None,
        width=100,
        height=100,
        resolution_x=res_x,
        resolution_y=res_y,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )

def test_temporal_alignment():
    tool = TemporalAlignmentTool()
    img_a = mock_rsimage("a.tif", acq_time="2024-01-01")
    img_b = mock_rsimage("b.tif", acq_time="2025-01-01")
    res = tool.execute(None, {"image_a": img_a, "image_b": img_b})
    assert res.success
    assert res.data["temporal_order"] == "before_after"

def test_spatial_alignment_diff_crs():
    tool = SpatialAlignmentTool()
    img_a = mock_rsimage("a.tif", crs="EPSG:4326")
    img_b = mock_rsimage("b.tif", crs="EPSG:3857")
    res = tool.execute(None, {"image_a": img_a, "image_b": img_b})
    assert res.success
    assert not res.data["compatible"]
    assert not res.data["same_crs"]

def test_spatial_alignment_diff_res():
    tool = SpatialAlignmentTool()
    img_a = mock_rsimage("a.tif", res_x=10, res_y=10)
    img_b = mock_rsimage("b.tif", res_x=20, res_y=20)
    res = tool.execute(None, {"image_a": img_a, "image_b": img_b})
    assert res.success
    assert not res.data["compatible"]
    assert not res.data["same_resolution"]
