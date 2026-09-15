import rasterio
from .models import RSImage
from .metadata import detect_modality, detect_sensor
from datetime import datetime

def _safe_transform(src):
    """Convert rasterio's Affine transform to a serialization-safe tuple of 6 scalars."""
    try:
        t = src.transform
        if t is None:
            return None
        try:
            return tuple(t)
        except TypeError:
            return (t.a, t.b, t.c, t.d, t.e, t.f)
    except TypeError:
        return None

def _safe_bounds(src, transform):
    """Compute bounds tuple from transform if available, otherwise None."""
    if transform is None:
        return None
    a, b, c, d, e, f = transform
    width = src.width
    height = src.height
    left = c
    top = f
    right = c + width * a
    bottom = f + height * e
    return (left, bottom, right, top)

def _safe_res(transform):
    """Extract (res_x, res_y) from transform tuple if available."""
    if transform is None:
        return None, None
    a, b, c, d, e, f = transform
    return a, abs(e)

def load_raster(path: str) -> RSImage:
    with rasterio.open(path) as src:
        meta = src.tags()
        acq_time = None

        modality = detect_modality(meta, src.descriptions)
        sensor = detect_sensor(meta)

        transform = _safe_transform(src)
        bounds = _safe_bounds(src, transform)
        res_x, res_y = _safe_res(transform)
        crs = src.crs.to_string() if src.crs else None

        return RSImage(
            path=path,
            modality=modality,
            sensor=sensor,
            acquisition_time=acq_time,
            crs=crs,
            bounds=bounds,
            transform=transform,
            width=src.width,
            height=src.height,
            resolution_x=res_x,
            resolution_y=res_y,
            band_count=src.count,
            band_names=list(src.descriptions) if any(src.descriptions) else [f"Band_{i}" for i in range(1, src.count+1)],
            nodata=src.nodata,
            dtype=src.dtypes[0] if src.dtypes else "unknown",
            metadata=meta
        )
