import numpy as np
import rasterio
from .normalization import normalize_array

def generate_preview(rs_image, band_indices=None):
    with rasterio.open(rs_image.path) as src:
        count = src.count
        
        if band_indices is None:
            if count >= 3:
                band_indices = [1, 2, 3] # default RGB assuming first 3 bands
            else:
                band_indices = [1] # Grayscale
                
        # Read the overview or full resolution if small
        overview_level = 1
        data = src.read(band_indices, out_shape=(
            len(band_indices),
            int(src.height // overview_level),
            int(src.width // overview_level)
        ))
        
        # Normalize
        normalized_data = np.zeros_like(data, dtype=np.float32)
        norm_meta = []
        for i in range(data.shape[0]):
            norm_band, meta = normalize_array(data[i], method="percentile")
            normalized_data[i] = norm_band
            norm_meta.append(meta)
            
        # Convert to 0-255 uint8
        preview_data = (normalized_data * 255).astype(np.uint8)
        
        return {
            "image": preview_data,
            "band_indices": band_indices,
            "normalization_metadata": norm_meta,
            "source_path": rs_image.path
        }
