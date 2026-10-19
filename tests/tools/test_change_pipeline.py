import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from satquery.agent.agent import SatQueryAgent
from satquery.inputs.raster_loader import load_raster
from satquery.tools.change_detection import ChangeDetectionTool
from satquery.tools.change_localization import ChangeLocalizationTool
from satquery.tools.spatial_alignment import SpatialAlignmentTool

# 100x100 px, 10 m pixels, UTM 43N (projected, so areas are exact).
ORIGIN_X, ORIGIN_Y, PIXEL = 500000.0, 1400000.0, 10.0
CRS = "EPSG:32643"


def write_raster(path, data, origin_x=ORIGIN_X, crs=CRS, nodata=None, tags=None):
    with rasterio.open(
        path, "w", driver="GTiff", height=data.shape[1], width=data.shape[2], count=data.shape[0],
        dtype=data.dtype, crs=crs, transform=from_origin(origin_x, ORIGIN_Y, PIXEL, PIXEL), nodata=nodata,
    ) as dst:
        dst.write(data)
        if tags:
            dst.update_tags(**tags)
    return str(path)


@pytest.fixture
def base_array():
    rng = np.random.default_rng(0)
    return rng.integers(0, 100, size=(3, 100, 100), dtype=np.uint8)


@pytest.fixture
def change_pair(tmp_path, base_array):
    """Before/after pair whose only difference is a 20x20 px block (rows 10-29, cols 60-79)."""
    after = base_array.copy()
    after[:, 10:30, 60:80] = 255
    return (write_raster(tmp_path / "before.tif", base_array),
            write_raster(tmp_path / "after.tif", after))


def test_change_detection_measures_real_change(change_pair):
    img_a, img_b = (load_raster(p) for p in change_pair)
    result = ChangeDetectionTool().execute(None, {"image_a": img_a, "image_b": img_b})

    assert result.success
    assert result.data["changed_pixel_count"] == 400
    assert result.data["valid_pixel_count"] == 10000
    assert result.data["change_percentage"] == 4.0
    assert result.data["mask"].shape == (100, 100)
    assert "mask" not in result.evidence[0].metadata


def test_change_detection_identical_images_report_no_change(tmp_path, base_array):
    path = write_raster(tmp_path / "same.tif", base_array)
    img = load_raster(path)
    result = ChangeDetectionTool().execute(None, {"image_a": img, "image_b": img})

    assert result.success
    assert result.data["change_percentage"] == 0.0


def test_change_detection_excludes_nodata(tmp_path, base_array):
    before = base_array.copy()
    before[before == 0] = 1
    before[:, :, :50] = 0  # left half is nodata
    after = before.copy()
    after[:, 10:30, 60:80] = 255
    img_a = load_raster(write_raster(tmp_path / "a.tif", before, nodata=0))
    img_b = load_raster(write_raster(tmp_path / "b.tif", after, nodata=0))

    result = ChangeDetectionTool().execute(None, {"image_a": img_a, "image_b": img_b})

    assert result.success
    assert result.data["valid_pixel_count"] == 5000
    assert result.data["changed_pixel_count"] == 400


def test_change_detection_downsamples_large_overlap(change_pair):
    img_a, img_b = (load_raster(p) for p in change_pair)
    result = ChangeDetectionTool().execute(None, {"image_a": img_a, "image_b": img_b, "max_size": 50})

    assert result.success
    assert result.data["grid_shape"] == (50, 50)
    assert result.data["valid_pixel_count"] == 2500
    assert result.data["change_percentage"] == pytest.approx(4.0, abs=0.5)
    assert any("downsampled" in w for w in result.warnings)


def test_change_detection_requires_inputs():
    result = ChangeDetectionTool().execute(None, {})
    assert not result.success


def test_change_localization_regions_and_area(change_pair):
    img_a, img_b = (load_raster(p) for p in change_pair)
    detection = ChangeDetectionTool().execute(None, {"image_a": img_a, "image_b": img_b}).data

    result = ChangeLocalizationTool().execute(None, {
        "mask": detection["mask"], "transform": detection["transform"], "crs": detection["crs"],
    })

    assert result.success
    assert result.data["changed_area_sqm"] == 40000.0  # 400 px * 100 m²
    assert result.data["region_count"] == 1
    expected = (ORIGIN_X + 60 * PIXEL, ORIGIN_Y - 30 * PIXEL, ORIGIN_X + 80 * PIXEL, ORIGIN_Y - 10 * PIXEL)
    assert result.data["regions"][0]["bounds"] == pytest.approx(expected)
    assert result.data["overall_change_bounds"] == pytest.approx(expected)


def test_change_localization_separates_regions(tmp_path, base_array):
    after = base_array.copy()
    after[:, 5:15, 5:15] = 255
    after[:, 70:90, 70:90] = 255
    img_a = load_raster(write_raster(tmp_path / "a.tif", base_array))
    img_b = load_raster(write_raster(tmp_path / "b.tif", after))
    detection = ChangeDetectionTool().execute(None, {"image_a": img_a, "image_b": img_b}).data

    result = ChangeLocalizationTool().execute(None, {
        "mask": detection["mask"], "transform": detection["transform"], "crs": detection["crs"],
    })

    assert result.data["region_count"] == 2
    assert [r["pixel_count"] for r in result.data["regions"]] == [400, 100]


def test_spatial_alignment_rejects_non_overlapping(tmp_path, base_array):
    img_a = load_raster(write_raster(tmp_path / "a.tif", base_array))
    img_b = load_raster(write_raster(tmp_path / "b.tif", base_array, origin_x=ORIGIN_X + 5000))

    result = SpatialAlignmentTool().execute(None, {"image_a": img_a, "image_b": img_b})

    assert not result.success
    assert "do not overlap" in result.errors[0]


def test_agent_change_analysis_end_to_end(change_pair):
    response = SatQueryAgent().run("What changed between before and after?", inputs=list(change_pair))

    assert "4.0%" in response.answer
    assert "40,000 m²" in response.answer
    tools = [ev.tool for ev in response.evidence]
    assert tools == ["temporal_alignment", "spatial_alignment", "change_detection",
                     "change_localization", "change_summary"]


def test_agent_change_analysis_stops_on_incompatible_pair(tmp_path, base_array):
    a = write_raster(tmp_path / "a.tif", base_array)
    b = write_raster(tmp_path / "b.tif", base_array, origin_x=ORIGIN_X + 5000)

    response = SatQueryAgent().run("Detect change between before and after", inputs=[a, b])

    assert response.answer.startswith("Failed due to errors")
    assert "do not overlap" in response.answer
    assert "change_detection" not in [ev.tool for ev in response.evidence]


def test_agent_reports_missing_input():
    response = SatQueryAgent().run("What is visible here?", inputs=["does_not_exist.tif"])

    assert response.answer.startswith("Failed due to errors")
    assert "does_not_exist.tif" in response.answer
    assert response.evidence == []


def test_agent_change_analysis_uses_acquisition_dates(tmp_path, base_array):
    after = base_array.copy()
    after[:, 10:30, 60:80] = 255
    earlier = write_raster(tmp_path / "x.tif", base_array, tags={"ACQUISITION_DATE": "2021-05-01"})
    later = write_raster(tmp_path / "y.tif", after, tags={"ACQUISITION_DATE": "2023-05-01"})

    # Passed in reverse order: the agent should reorder by date and say so.
    response = SatQueryAgent().run("What changed after construction?", inputs=[later, earlier])

    assert "Acquisition order: 2021-05-01 00:00:00 -> 2023-05-01 00:00:00." in response.answer
    assert any("reverse chronological order" in lim for lim in response.limitations)
