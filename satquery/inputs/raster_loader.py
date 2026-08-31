import rasterio
from .models import RSImage
from .metadata import detect_modality, detect_sensor
from datetime import datetime

def load_raster(path: str) -> RSImage:
    with rasterio.open(path) as src:
        bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top) if src.bounds else None
        res_x, res_y = src.res if src.res else (None, None)
        crs = src.crs.to_string() if src.crs else None
        
        meta = src.tags()
        acq_time = None
        
        modality = detect_modality(meta, src.descriptions)
        sensor = detect_sensor(meta)
        
        return RSImage(
            path=path,
            modality=modality,
            sensor=sensor,
            acquisition_time=acq_time,
            crs=crs,
            bounds=bounds,
            transform=src.transform,
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
