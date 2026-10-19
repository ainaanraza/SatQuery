import numpy as np

from .registration import read_on_grid

# Band-description aliases (Sentinel-2 / generic names). Landsat "B5" is NIR but
# Sentinel-2 "B5" is red edge, so it is deliberately not treated as NIR.
GREEN_ALIASES = ("green", "b3", "b03")
NIR_ALIASES = ("nir", "b8", "b08", "nir08")


def find_band(image, aliases):
    """1-based index of the first band whose description matches an alias, or None."""
    for i, name in enumerate(image.band_names):
        tokens = str(name).lower().replace("-", "_").replace(" ", "_").split("_")
        if str(name).lower() in aliases or any(t in aliases for t in tokens):
            return i + 1
    return None


def preprocess_optical(image, bounds=None, shape=None):
    """Read optical bands onto a grid; compute NDWI when green and NIR bands can be identified."""
    bounds = bounds or image.bounds
    shape = shape or (image.height, image.width)
    green, nir = find_band(image, GREEN_ALIASES), find_band(image, NIR_ALIASES)

    bands = [green, nir] if green and nir else list(range(1, min(image.band_count, 3) + 1))
    raw = read_on_grid(image, bounds, bands, shape)
    valid = ~np.ma.getmaskarray(raw).any(axis=0)
    data = np.ma.getdata(raw).astype(np.float32)
    valid &= np.isfinite(data).all(axis=0)

    ndwi = None
    if green and nir:
        g, n = data[0], data[1]
        denom = g + n
        with np.errstate(divide="ignore", invalid="ignore"):
            ndwi = np.where(denom != 0, (g - n) / denom, np.nan).astype(np.float32)
        valid &= np.isfinite(ndwi)
        ndwi[~valid] = np.nan

    return {
        "data": data,
        "valid": valid,
        "ndwi": ndwi,
        "method": "ndwi" if ndwi is not None else "no_water_index",
        "bands_used": {"green": image.band_names[green - 1], "nir": image.band_names[nir - 1]} if ndwi is not None else {},
        "source": image.path,
    }
