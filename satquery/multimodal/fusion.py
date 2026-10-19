import numpy as np

from .models import FusionResult

DEFAULT_SAR_WATER_DB = -18.0
DEFAULT_NDWI_WATER = 0.0


def otsu_threshold(values, bins=256):
    """Otsu's threshold for a 1-D array (maximises between-class variance)."""
    hist, edges = np.histogram(values, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    weight_low = np.cumsum(hist)
    weight_high = weight_low[-1] - weight_low
    sum_low = np.cumsum(hist * centers)
    mean_low = np.divide(sum_low, weight_low, out=np.zeros_like(sum_low, dtype=float), where=weight_low > 0)
    mean_high = np.divide(sum_low[-1] - sum_low, weight_high, out=np.zeros_like(sum_low, dtype=float), where=weight_high > 0)
    between = weight_low * weight_high * (mean_low - mean_high) ** 2
    return float(centers[np.argmax(between)])


def fuse_deterministic(optical_rep, sar_rep, sar_threshold_db=DEFAULT_SAR_WATER_DB, ndwi_threshold=DEFAULT_NDWI_WATER):
    """Rule-based optical/SAR water fusion on co-registered grids. Not a neural network.

    SAR: water where backscatter is below `sar_threshold_db` (calibrated data) or below
    an Otsu threshold (uncalibrated DNs). Optical: water where NDWI > `ndwi_threshold`,
    if NDWI is available. Reports per-sensor water fractions and their agreement.
    """
    sar = sar_rep["data"]
    valid = sar_rep["valid"] & optical_rep["valid"]
    if not valid.any():
        raise ValueError("No pixels are valid in both the optical and SAR images.")

    if sar_rep["calibration"] == "uncalibrated_dn":
        sar_threshold = otsu_threshold(sar[valid])
        sar_threshold_method = "otsu_on_dn"
    else:
        sar_threshold = sar_threshold_db
        sar_threshold_method = "fixed_db"
    sar_water = (sar < sar_threshold) & valid

    ndwi = optical_rep.get("ndwi")
    optical_water = (ndwi > ndwi_threshold) & valid if ndwi is not None else None

    n_valid = int(valid.sum())
    pct = lambda mask: round(100.0 * int(mask.sum()) / n_valid, 2)

    stats = {
        "valid_pixel_count": n_valid,
        "sar_band": sar_rep["band"],
        "sar_calibration": sar_rep["calibration"],
        "sar_threshold": round(sar_threshold, 3),
        "sar_threshold_method": sar_threshold_method,
        "sar_water_pixel_count": int(sar_water.sum()),
        "sar_water_percentage": pct(sar_water),
        "optical_water_index": optical_rep["method"],
        "optical_bands_used": optical_rep.get("bands_used", {}),
    }
    if optical_water is not None:
        stats.update({
            "ndwi_threshold": ndwi_threshold,
            "optical_water_pixel_count": int(optical_water.sum()),
            "optical_water_percentage": pct(optical_water),
            "both_water_percentage": pct(sar_water & optical_water),
            "sar_only_water_percentage": pct(sar_water & ~optical_water),
            "optical_only_water_percentage": pct(optical_water & ~sar_water),
            "agreement_percentage": pct((sar_water == optical_water) & valid),
        })

    return FusionResult(
        fusion_method="sar_backscatter_ndwi_agreement" if optical_water is not None else "sar_backscatter_only",
        provenance_optical=optical_rep["source"] if optical_rep else None,
        provenance_sar=sar_rep["source"] if sar_rep else None,
        data={"statistics": stats, "sar_water_mask": sar_water, "optical_water_mask": optical_water, "valid": valid},
    )
