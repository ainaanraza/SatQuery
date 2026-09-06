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


def test_cloud_region_is_not_counted_as_change(tmp_path):
    t1_data = np.array([
        [10, 20],
        [30, 40]
    ], dtype=np.uint8)

    t2_data = np.array([
        [10, 200],
        [30, 40]
    ], dtype=np.uint8)

    # Treat the top-right pixel as a cloud/invalid region.
    # It has different values between T1 and T2, but must not
    # be considered a real change.
    t1_data[0, 1] = 0
    t2_data[0, 1] = 0

    # Introduce one genuine change outside the cloud.
    t2_data[1, 1] = 100

    t1_path = tmp_path / "t1_cloud.tif"
    t2_path = tmp_path / "t2_cloud.tif"

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


def test_shadow_like_darkening_is_not_treated_as_widespread_change(tmp_path):
    t1_data = np.array([
        [100, 100, 100, 100],
        [100, 100, 100, 100],
        [100, 100, 100, 100],
        [100, 100, 100, 100]
    ], dtype=np.uint8)

    # T2 has a broad darkening that represents a shadow/acquisition effect.
    t2_data = np.array([
        [50, 50, 50, 50],
        [50, 50, 50, 50],
        [100, 100, 100, 100],
        [100, 100, 100, 100]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1_shadow.tif"
    t2_path = tmp_path / "t2_shadow.tif"

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

    # A broad uniform darkening should not be interpreted as
    # widespread semantic change.
    assert result.data["change_percentage"] < 50.0


def test_seasonal_variation_is_not_treated_as_widespread_change(tmp_path):
    t1_data = np.array([
        [100, 110, 120, 130],
        [110, 120, 130, 140],
        [120, 130, 140, 150],
        [130, 140, 150, 160]
    ], dtype=np.uint8)

    # Simulate broad seasonal reflectance variation.
    t2_data = t1_data + 20

    t1_path = tmp_path / "t1_seasonal.tif"
    t2_path = tmp_path / "t2_seasonal.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data.astype(np.uint8))

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

    # A broad uniform seasonal variation should not be treated
    # as widespread semantic change.
    assert result.data["change_percentage"] < 50.0      


def test_illumination_change_is_not_treated_as_widespread_change(tmp_path):
    t1_data = np.array([
        [80, 90, 100, 110],
        [90, 100, 110, 120],
        [100, 110, 120, 130],
        [110, 120, 130, 140]
    ], dtype=np.uint8)

    # Simulate a broad illumination/acquisition-condition change.
    t2_data = t1_data + 30

    t1_path = tmp_path / "t1_illumination.tif"
    t2_path = tmp_path / "t2_illumination.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data.astype(np.uint8))

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

    # A broad illumination change should not be interpreted
    # as widespread semantic change.
    assert result.data["change_percentage"] < 50.0    


def test_registration_shift_is_rejected(tmp_path):
    t1_data = np.array([
        [10, 20, 30],
        [40, 50, 60],
        [70, 80, 90]
    ], dtype=np.uint8)

    t2_data = np.array([
        [20, 30, 40],
        [50, 60, 70],
        [80, 90, 100]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1_shift.tif"
    t2_path = tmp_path / "t2_shift.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    # Simulate a registration error by giving T2 a different
    # geographic pixel grid.
    with rasterio.open(t2_path, "r+") as src:
        src.transform = rasterio.transform.from_origin(
            0.5, 2, 1, 1
        )

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is False
    assert "geographic pixel grid" in result.errors[0]    


def test_resolution_difference_is_rejected(tmp_path):
    t1_data = np.ones((2, 2), dtype=np.uint8) * 100
    t2_data = np.ones((2, 2), dtype=np.uint8) * 100

    t1_path = tmp_path / "t1_resolution.tif"
    t2_path = tmp_path / "t2_resolution.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    # Same dimensions, but different pixel size / GSD.
    with rasterio.open(t2_path, "r+") as src:
        src.transform = rasterio.transform.from_origin(
            0, 2, 2, 2
        )

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is False
    assert "geographic pixel grid" in result.errors[0]    



def test_partial_footprint_is_rejected(tmp_path):
    t1_data = np.ones((2, 2), dtype=np.uint8) * 100
    t2_data = np.ones((2, 2), dtype=np.uint8) * 100

    t1_path = tmp_path / "t1_partial.tif"
    t2_path = tmp_path / "t2_partial.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    # Move T2 so its footprint does not match T1.
    with rasterio.open(t2_path, "r+") as src:
        src.transform = rasterio.transform.from_origin(
            2, 2, 1, 1
        )

    tool = ChangeDetectionTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": mock_rsimage(t1_path),
            "image_b": mock_rsimage(t2_path),
            "method": "absolute_difference"
        }
    )

    assert result.success is False
    assert "geographic pixel grid" in result.errors[0]      
