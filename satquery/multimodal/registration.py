import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.windows import from_bounds as window_from_bounds

DEFAULT_MAX_SIZE = 2048


def overlap_bounds(img_a, img_b):
    """Intersection of two images' bounds, or None if they do not overlap."""
    a_minx, a_miny, a_maxx, a_maxy = img_a.bounds
    b_minx, b_miny, b_maxx, b_maxy = img_b.bounds
    bounds = (max(a_minx, b_minx), max(a_miny, b_miny), min(a_maxx, b_maxx), min(a_maxy, b_maxy))
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        return None
    return bounds


def common_grid(reference, other, max_size=DEFAULT_MAX_SIZE):
    """Pixel grid covering the overlap of two same-CRS images at `reference`'s resolution.

    Downsampled so neither side exceeds `max_size` pixels. Raises ValueError if the
    images cannot be co-registered (different CRS or no overlap).
    """
    if reference.crs != other.crs:
        raise ValueError(f"CRS mismatch ({reference.crs} vs {other.crs}); reprojection is not supported yet.")
    bounds = overlap_bounds(reference, other)
    if bounds is None:
        raise ValueError("Images do not overlap spatially.")

    width = max(1, round((bounds[2] - bounds[0]) / abs(reference.resolution_x)))
    height = max(1, round((bounds[3] - bounds[1]) / abs(reference.resolution_y)))
    downsample = max(1.0, max(width, height) / max_size)
    shape = (max(1, round(height / downsample)), max(1, round(width / downsample)))
    return {
        "bounds": bounds,
        "shape": shape,
        "transform": transform_from_bounds(*bounds, shape[1], shape[0]),
        "downsample_factor": round(downsample, 3),
        "crs": reference.crs,
    }


def read_on_grid(image, bounds, bands, shape):
    """Read 1-based `bands` of `image` over `bounds`, area-averaged onto a grid of `shape`, as a masked array."""
    with rasterio.open(image.path) as src:
        window = window_from_bounds(*bounds, transform=src.transform)
        return src.read(
            list(bands),
            window=window,
            out_shape=(len(bands), shape[0], shape[1]),
            resampling=Resampling.average,
            masked=True,
        )


class RegistrationStrategy:
    def validate_and_register(self, img_a, img_b):
        if img_a.crs != img_b.crs:
            return False, "CRS mismatch"
        if overlap_bounds(img_a, img_b) is None:
            return False, "No spatial overlap"
        return True, "Aligned"
