import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from satquery.agent.agent import SatQueryAgent
from satquery.inputs.metadata import detect_modality
from satquery.inputs.raster_loader import load_raster
from satquery.multimodal.fusion import otsu_threshold
from satquery.tools.optical_sar_fusion import OpticalSARFusionTool

ORIGIN_X, ORIGIN_Y, PIXEL, CRS = 500000.0, 1400000.0, 10.0, "EPSG:32643"


def write_raster(path, data, descriptions=None, origin_x=ORIGIN_X):
    with rasterio.open(
        path, "w", driver="GTiff", height=data.shape[1], width=data.shape[2], count=data.shape[0],
        dtype=data.dtype, crs=CRS, transform=from_origin(origin_x, ORIGIN_Y, PIXEL, PIXEL),
    ) as dst:
        dst.write(data)
        for i, name in enumerate(descriptions or [], start=1):
            dst.set_band_description(i, name)
    return str(path)


@pytest.fixture
def optical(tmp_path):
    """Sentinel-2-like bands; water (high green, low NIR) in rows 20-39, cols 20-59 = 800 px."""
    data = np.zeros((4, 100, 100), dtype=np.uint16)
    data[0], data[1], data[2], data[3] = 600, 800, 700, 3000
    data[1, 20:40, 20:60], data[3, 20:40, 20:60] = 1200, 300
    return write_raster(tmp_path / "optical.tif", data, ["B2", "B3", "B4", "B8"])


def sar_array(dtype, land, water):
    """SAR water in rows 20-39, cols 20-69 = 1000 px (200 px more than optical: SAR-only water)."""
    data = np.full((1, 100, 100), land, dtype=dtype)
    data[0, 20:40, 20:70] = water
    return data


@pytest.fixture
def sar_db(tmp_path):
    return write_raster(tmp_path / "sar_db.tif", sar_array(np.float32, -8.0, -22.0), ["VV"])


def run_fusion(optical_path, sar_path, **kwargs):
    return OpticalSARFusionTool().execute(None, {
        "optical_image": load_raster(optical_path), "sar_image": load_raster(sar_path), **kwargs,
    })


def test_fusion_water_statistics(optical, sar_db):
    result = run_fusion(optical, sar_db)

    assert result.success, result.errors
    stats = result.data["statistics"]
    assert stats["sar_calibration"] == "db"
    assert stats["sar_water_percentage"] == 10.0
    assert stats["optical_water_percentage"] == 8.0
    assert stats["both_water_percentage"] == 8.0
    assert stats["sar_only_water_percentage"] == 2.0
    assert stats["optical_only_water_percentage"] == 0.0
    assert stats["agreement_percentage"] == 98.0
    assert stats["optical_bands_used"] == {"green": "B3", "nir": "B8"}
    assert result.data["sar_water_area_sqm"] == 100000.0
    assert result.data["sar_water_region_count"] == 1
    assert result.data["sar_water_regions"][0]["bounds"] == pytest.approx(
        (ORIGIN_X + 200, ORIGIN_Y - 400, ORIGIN_X + 700, ORIGIN_Y - 200))
    assert "sar_water_mask" not in result.evidence[0].metadata


def test_fusion_linear_power_sar_converted_to_db(tmp_path, optical):
    sar = write_raster(tmp_path / "sar_lin.tif", sar_array(np.float32, 0.15, 0.005), ["VV"])
    stats = run_fusion(optical, sar).data["statistics"]

    assert stats["sar_calibration"] == "linear_power"
    assert stats["sar_water_percentage"] == 10.0


def test_fusion_uncalibrated_sar_uses_otsu(tmp_path, optical):
    sar = write_raster(tmp_path / "sar_dn.tif", sar_array(np.uint8, 120, 20), ["VV"])
    result = run_fusion(optical, sar)

    assert result.data["statistics"]["sar_threshold_method"] == "otsu_on_dn"
    assert result.data["statistics"]["sar_water_percentage"] == 10.0
    assert any("uncalibrated" in w for w in result.warnings)


def test_fusion_swaps_inputs_by_detected_modality(optical, sar_db):
    result = OpticalSARFusionTool().execute(None, {
        "optical_image": load_raster(sar_db), "sar_image": load_raster(optical),
    })

    assert result.success
    assert result.data["sar_source"] == sar_db
    assert result.data["statistics"]["sar_water_percentage"] == 10.0


def test_fusion_without_nir_is_sar_only(tmp_path, sar_db):
    rgb = write_raster(tmp_path / "rgb.tif", np.full((3, 100, 100), 100, dtype=np.uint8))
    result = run_fusion(rgb, sar_db)

    assert result.success
    assert result.data["fusion_method"] == "sar_backscatter_only"
    assert "optical_water_percentage" not in result.data["statistics"]
    assert any("NDWI unavailable" in w for w in result.warnings)


def test_otsu_threshold_separates_modes():
    values = np.concatenate([np.full(900, 120.0), np.full(100, 20.0)])
    assert 20 < otsu_threshold(values) < 120


def test_detect_modality_from_band_names():
    assert detect_modality({}, ["VV", "VH"]) == "sar"
    assert detect_modality({}, ["B2", "B3", "B4", "B8"]) == "optical"
    assert detect_modality({}, [None, None]) == "unknown"


def test_agent_fusion_end_to_end(optical, sar_db):
    response = SatQueryAgent().run("Map water using the SAR and optical images", inputs=[optical, sar_db])

    assert "marks 10.0% of 10,000 co-registered pixels as water" in response.answer
    assert "agree on 98.0% of pixels" in response.answer
    assert [ev.tool for ev in response.evidence] == ["spatial_alignment", "optical_sar_fusion"]


def test_agent_fusion_rejects_non_overlapping(tmp_path, optical):
    far_sar = write_raster(tmp_path / "far.tif", sar_array(np.float32, -8.0, -22.0), ["VV"], origin_x=ORIGIN_X + 5000)
    response = SatQueryAgent().run("Fuse SAR and optical", inputs=[optical, far_sar])

    assert response.answer.startswith("Failed due to errors")
    assert "do not overlap" in response.answer


def test_fusion_refuses_when_no_input_looks_like_sar(tmp_path, optical):
    rgb = write_raster(tmp_path / "rgb.tif", np.full((3, 100, 100), 100, dtype=np.uint8))
    result = run_fusion(optical, rgb)

    assert not result.success
    assert "Could not identify a SAR image" in result.errors[0]


def test_fusion_refuses_two_sar_images(tmp_path, sar_db):
    other = write_raster(tmp_path / "sar2.tif", sar_array(np.float32, -8.0, -22.0), ["VH"])
    result = run_fusion(other, sar_db)

    assert not result.success
    assert "Both inputs were detected as sar" in result.errors[0]
