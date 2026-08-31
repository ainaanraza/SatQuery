from .models import RSImage

def detect_modality(metadata: dict, band_names: list) -> str:
    modality = "unknown"
    if "sensor" in metadata:
        s = metadata["sensor"].lower()
        if "sentinel-1" in s or "sar" in s:
            modality = "sar"
        elif "sentinel-2" in s or "optical" in s:
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
