import numpy as np

from .registration import read_on_grid

# Preferred polarisations for water detection (co-pol first).
SAR_BAND_PRIORITY = ("vv", "hh", "vh", "hv")


def select_sar_band(image):
    """1-based index and name of the best SAR band, by description; falls back to band 1."""
    names = [str(n).lower() for n in image.band_names]
    for pol in SAR_BAND_PRIORITY:
        for i, name in enumerate(names):
            if pol in name.replace("_", " ").replace("-", " ").split() or name == pol:
                return i + 1, pol.upper()
    return 1, image.band_names[0] if image.band_names else "Band_1"


def preprocess_sar(image, bounds=None, shape=None):
    """Read one SAR band onto a grid and express it in dB where the calibration allows.

    calibration is "db" (float data with negative values, already in dB),
    "linear_power" (non-negative float, converted with 10*log10), or
    "uncalibrated_dn" (integer digital numbers; left as-is, so only relative
    thresholds are meaningful).
    """
    bounds = bounds or image.bounds
    shape = shape or (image.height, image.width)
    band_index, band_name = select_sar_band(image)

    raw = read_on_grid(image, bounds, [band_index], shape)[0]
    valid = ~np.ma.getmaskarray(raw)
    data = np.ma.getdata(raw).astype(np.float32)
    valid &= np.isfinite(data)

    if np.issubdtype(np.dtype(image.dtype), np.floating):
        if valid.any() and (data[valid] < 0).any():
            calibration = "db"
        else:
            calibration = "linear_power"
            with np.errstate(divide="ignore"):
                data = 10.0 * np.log10(np.maximum(data, 1e-6))
    else:
        calibration = "uncalibrated_dn"

    data[~valid] = np.nan
    return {
        "data": data,
        "valid": valid,
        "method": "log_db_transform" if calibration != "uncalibrated_dn" else "raw_dn",
        "calibration": calibration,
        "band": band_name,
        "source": image.path,
    }
