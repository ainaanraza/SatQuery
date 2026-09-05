from datetime import datetime

from satquery.tools.temporal_alignment import TemporalAlignmentTool
from satquery.inputs.models import RSImage


def mock_rsimage(path, acquisition_time):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=acquisition_time,
        crs="EPSG:4326",
        bounds=(0, 0, 10, 10),
        transform=None,
        width=100,
        height=100,
        resolution_x=1,
        resolution_y=1,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )


def test_temporal_alignment_before_after():
    tool = TemporalAlignmentTool()

    image_a = mock_rsimage(
        "before.tif",
        datetime(2024, 1, 1)
    )

    image_b = mock_rsimage(
        "after.tif",
        datetime(2025, 1, 1)
    )

    result = tool.execute(
        context=None,
        arguments={
            "image_a": image_a,
            "image_b": image_b
        }
    )

    assert result.success is True
    assert result.data["temporal_order"] == "before_after"
    assert result.data["before_time"] == datetime(2024, 1, 1)
    assert result.data["after_time"] == datetime(2025, 1, 1)
    assert len(result.evidence) >= 1