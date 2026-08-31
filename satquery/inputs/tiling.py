import numpy as np
import rasterio
from dataclasses import dataclass
from typing import Tuple

@dataclass
class RasterWindow:
    col_off: int
    row_off: int
    width: int
    height: int

@dataclass
class RasterTile:
    data: np.ndarray
    window: RasterWindow
    transform: rasterio.transform.Affine

def iter_tiles(image, tile_size=512, overlap=0):
    with rasterio.open(image.path) as src:
        width = src.width
        height = src.height
        step = tile_size - overlap
        if step <= 0:
            raise ValueError("Overlap must be less than tile size")
        
        for row_off in range(0, height, step):
            for col_off in range(0, width, step):
                w = min(tile_size, width - col_off)
                h = min(tile_size, height - row_off)
                
                window = rasterio.windows.Window(col_off, row_off, w, h)
                data = src.read(window=window)
                transform = rasterio.windows.transform(window, src.transform)
                
                yield RasterTile(
                    data=data,
                    window=RasterWindow(col_off, row_off, w, h),
                    transform=transform
                )
