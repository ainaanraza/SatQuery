import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from .models import RSImage

SAR_BAND_TOKENS = {"vv", "vh", "hh", "hv"}
OPTICAL_BAND_TOKENS = {"red", "green", "blue", "nir", "swir", "b2", "b3", "b4", "b8", "b02", "b03", "b04", "b08"}

def detect_modality(metadata: dict, band_names: list) -> str:
    modality = "unknown"
    if "sensor" in metadata:
        s = metadata["sensor"].lower()
        if "sentinel-1" in s or "sar" in s:
            modality = "sar"
        elif "sentinel-2" in s or "optical" in s:
            modality = "optical"
    if modality == "unknown" and band_names:
        # Fall back to band descriptions, e.g. "VV"/"VH" (SAR) or "B3"/"NIR" (optical).
        tokens = set()
        for name in band_names:
            if name:
                tokens.update(re.split(r"[\s_\-]+", str(name).lower()))
        if tokens & SAR_BAND_TOKENS:
            modality = "sar"
        elif tokens & OPTICAL_BAND_TOKENS:
            modality = "optical"
    return modality

def detect_sensor(metadata: dict) -> str:
    sensor = "unknown"
    if "sensor" in metadata:
        s = metadata["sensor"].lower()
        if "sentinel-1" in s:
            sensor = "Sentinel-1"
        elif "sentinel-2" in s:
            sensor = "Sentinel-2"
        elif "cartosat" in s:
            sensor = "Cartosat-2S"
        elif "risat" in s:
            sensor = "RISAT"
    return sensor

# Tags that explicitly record when the scene was captured, in priority order (matched case-insensitively).
ACQUISITION_TAGS = [
    "ACQUISITION_DATETIME", "ACQUISITION_DATE", "ACQUISITION_TIME", "DATE_ACQUIRED",
    "SENSING_TIME", "SENSING_START", "DATATAKE_1_DATATAKE_SENSING_START",
    "PRODUCT_START_TIME", "FIRST_LINE_TIME", "SCENE_CENTER_TIME_DATE",
]
# TIFFTAG_DATETIME is often the file processing time, so it is only a last resort.
FALLBACK_TAGS = ["TIFFTAG_DATETIME"]

_DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
    "%Y:%m:%d %H:%M:%S", "%Y-%m-%d", "%Y%m%dT%H%M%S", "%Y%m%d",
]
# Dates embedded in Sentinel/Landsat-style product names, e.g. S2A_MSIL2A_20230115T053211_...
_FILENAME_DATE = re.compile(r"(?<!\d)((?:19|20)\d{6})(?:T(\d{6}))?(?!\d)")


def parse_datetime(value) -> Optional[datetime]:
    """Parse common remote-sensing timestamp formats; aware values are converted to naive UTC."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    tz_offset = None
    if text.endswith("Z"):
        text, tz_offset = text[:-1], timezone.utc
    else:
        match = re.search(r"([+-]\d{2}):?(\d{2})$", text)
        if match and ("T" in text or " " in text):
            sign = 1 if match.group(1)[0] == "+" else -1
            hours, minutes = int(match.group(1)[1:]), int(match.group(2))
            tz_offset = timezone(sign * timedelta(hours=hours, minutes=minutes))
            text = text[:match.start()]
    if "." in text:
        head, frac = text.rsplit(".", 1)
        if frac.isdigit():
            text = f"{head}.{frac[:6]}"
    for fmt in _DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if tz_offset is not None:
            parsed = parsed.replace(tzinfo=tz_offset).astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    return None


def detect_acquisition_time(metadata: dict, path: str = "") -> Tuple[Optional[datetime], Optional[str]]:
    """Return (acquisition_time, source) where source names the tag or 'filename' it came from."""
    upper = {str(k).upper(): v for k, v in metadata.items()}
    for tag in ACQUISITION_TAGS:
        parsed = parse_datetime(upper.get(tag))
        if parsed:
            return parsed, tag
    if path:
        for match in _FILENAME_DATE.finditer(os.path.basename(path)):
            stamp = match.group(1) + (f"T{match.group(2)}" if match.group(2) else "")
            parsed = parse_datetime(stamp)
            if parsed:
                return parsed, "filename"
    for tag in FALLBACK_TAGS:
        parsed = parse_datetime(upper.get(tag))
        if parsed:
            return parsed, tag
    return None, None
