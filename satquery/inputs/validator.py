from dataclasses import dataclass, field
from typing import List, Dict
import os
from .models import RSImage

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    checks: Dict[str, bool] = field(default_factory=dict)

def validate_image(image: RSImage) -> ValidationResult:
    errors = []
    warnings = []
    checks = {
        "file_readable": True,
        "raster_valid": True,
        "crs_available": True,
        "bounds_valid": True,
    }

    if not os.path.exists(image.path):
        errors.append(f"File {image.path} does not exist.")
        checks["file_readable"] = False

    if image.width <= 0 or image.height <= 0:
        errors.append("Raster dimensions invalid.")
        checks["raster_valid"] = False

    if not image.crs:
        warnings.append("CRS is not available.")
        checks["crs_available"] = False

    if not image.bounds:
        warnings.append("Bounds are not valid.")
        checks["bounds_valid"] = False

    if image.acquisition_time is None:
        warnings.append("Acquisition time unavailable.")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        checks=checks
    )


def validate_raster_input(path: str) -> ValidationResult:
    errors = []
    checks = {}
    supported_extensions = {".tif", ".tiff", ".geotiff", ".img", ".bil", ".bip", ".bsq"}

    if not os.path.exists(path):
        errors.append(f"File {path} does not exist.")
        checks["file_readable"] = False
    else:
        checks["file_readable"] = True

    ext = os.path.splitext(path)[1].lower()
    if ext not in supported_extensions:
        errors.append(f"Unsupported file type: {ext}")
        checks["raster_valid"] = False
    else:
        checks["raster_valid"] = True

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=[],
        checks=checks
    )
