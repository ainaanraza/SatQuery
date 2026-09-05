from rasterio.transform import from_origin
from satquery.tools.spatial_alignment import SpatialAlignmentTool
from satquery.inputs.models import RSImage


def mock_rsimage(
    path,
    crs="EPSG:4326",
    resolution_x=1,
    resolution_y=1,
    bounds=(0, 0, 10, 10),
    transform=None
):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=None,
        crs=crs,
        bounds=bounds,
        transform=transform,
        width=100,
        height=100,
        resolution_x=resolution_x,
        resolution_y=resolution_y,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )


def test_spatial_alignment_compatible():
    tool = SpatialAlignmentTool()

    image_a = mock_rsimage("t1.tif")
    image_b = mock_rsimage("t2.tif")

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["same_crs"] is True
    assert result.data["same_resolution"] is True
    assert result.data["overlap"] is True
    assert result.data["compatible"] is True


def test_spatial_alignment_different_crs():
    tool = SpatialAlignmentTool()

    image_a = mock_rsimage("t1.tif", crs="EPSG:4326")
    image_b = mock_rsimage("t2.tif", crs="EPSG:3857")

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["same_crs"] is False
    assert result.data["compatible"] is False


def test_spatial_alignment_different_resolution():
    tool = SpatialAlignmentTool()

    image_a = mock_rsimage("t1.tif", resolution_x=1, resolution_y=1)
    image_b = mock_rsimage("t2.tif", resolution_x=2, resolution_y=2)

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["same_resolution"] is False
    assert result.data["compatible"] is False


def test_spatial_alignment_no_overlap():
    tool = SpatialAlignmentTool()

    image_a = mock_rsimage(
        "t1.tif",
        bounds=(0, 0, 10, 10)
    )

    image_b = mock_rsimage(
        "t2.tif",
        bounds=(20, 20, 30, 30)
    )

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["overlap"] is False
    assert result.data["compatible"] is False


def test_different_pixel_grid_is_incompatible():
    image_a = mock_rsimage(
        "a.tif",
        crs="EPSG:4326",
        resolution_x=1,
        resolution_y=1,
        bounds=(0, 0, 10, 10),
        transform=from_origin(0, 10, 1, 1)
    )

    image_b = mock_rsimage(
        "b.tif",
        crs="EPSG:4326",
        resolution_x=1,
        resolution_y=1,
        bounds=(0, 0, 10, 10),
        transform=from_origin(0.5, 10, 1, 1)
    )

    tool = SpatialAlignmentTool()

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["grid_aligned"] is False
    assert result.data["compatible"] is False    