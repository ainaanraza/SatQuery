import pytest
from satquery.inputs.models import RSImage
from satquery.inputs.validator import validate_image

def test_validate_image_invalid_path():
    img = RSImage(
        path="nonexistent.tif", modality=None, sensor=None, acquisition_time=None,
        crs=None, bounds=None, transform=None, width=10, height=10, resolution_x=1,
        resolution_y=1, band_count=1, band_names=[], nodata=None, dtype="uint8", metadata={}
    )
    val = validate_image(img)
    assert not val.valid
    assert not val.checks["file_readable"]
