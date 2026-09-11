import pytest
import tempfile
import os
from satquery.inputs.models import RSImage
from satquery.inputs.validator import validate_image, validate_raster_input

def test_validate_image_invalid_path():
    img = RSImage(
        path="nonexistent.tif", modality=None, sensor=None, acquisition_time=None,
        crs=None, bounds=None, transform=None, width=10, height=10, resolution_x=1,
        resolution_y=1, band_count=1, band_names=[], nodata=None, dtype="uint8", metadata={}
    )
    val = validate_image(img)
    assert not val.valid
    assert not val.checks["file_readable"]


def test_validate_raster_input_missing():
    """A missing input path produces a validation error."""
    val = validate_raster_input("nonexistent_file.tif")
    assert not val.valid
    assert len(val.errors) > 0
    assert any("does not exist" in e for e in val.errors)


def test_validate_raster_input_unsupported():
    """An unsupported file type produces a validation error."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not a raster")
        path = f.name
    try:
        val = validate_raster_input(path)
        assert not val.valid
        assert len(val.errors) > 0
        assert any("Unsupported file type" in e for e in val.errors)
    finally:
        os.unlink(path)


def test_validate_raster_input_valid_tif():
    """A file with a supported raster extension passes validation (file may not exist as raster)."""
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        f.write(b"fake raster data")
        path = f.name
    try:
        val = validate_raster_input(path)
        # The file exists so file_readable is True; .tif extension is supported so raster_valid is True
        assert val.valid
        assert val.checks["file_readable"]
        assert val.checks["raster_valid"]
    finally:
        os.unlink(path)
