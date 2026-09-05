import numpy as np
import rasterio
from rasterio.transform import from_origin

from satquery.tools.change_detection import ChangeDetectionTool
from satquery.inputs.models import RSImage


def create_test_raster(path, data):
    transform = from_origin(0, 2, 1, 1)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        nodata=0,
        transform=transform,
    ) as dst:
        dst.write(data, 1)


def mock_rsimage(path):
    return RSImage(
        path=str(path),
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=None,
        crs="EPSG:4326",
        bounds=(0, 0, 2, 2),
        transform=from_origin(0, 2, 1, 1),
        width=2,
        height=2,
        resolution_x=1,
        resolution_y=1,
        band_count=1,
        band_names=["B1"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )


def test_identical_images_have_no_change(tmp_path):
    image_data = np.array([
        [10, 20],
        [30, 40]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1.tif"
    t2_path = tmp_path / "t2.tif"

    create_test_raster(t1_path, image_data)
    create_test_raster(t2_path, image_data)

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is True
    assert result.data["change_percentage"] == 0.0


def test_changed_pixel_is_detected(tmp_path):
    t1_data = np.array([
        [10, 20],
        [30, 40]
    ], dtype=np.uint8)

    t2_data = np.array([
        [10, 20],
        [30, 100]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1.tif"
    t2_path = tmp_path / "t2.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is True
    assert result.data["changed_pixel_count"] == 1
    assert result.data["change_percentage"] == 25.0


def test_nodata_pixel_is_not_counted_as_change(tmp_path):
    t1_data = np.array([
        [10, 20],
        [30, 40]
    ], dtype=np.uint8)

    t2_data = np.array([
        [10, 20],
        [30, 0]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1.tif"
    t2_path = tmp_path / "t2.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is True
    assert result.data["changed_pixel_count"] == 0
    assert result.data["change_percentage"] == 0.0