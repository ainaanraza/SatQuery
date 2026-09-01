import numpy as np
import rasterio
from rasterio.transform import from_origin

def create_sample_geotiff(filename="demo_satellite.tif"):
    width, height = 512, 512
    # Create 3-band RGB satellite simulation (vegetation, water, urban)
    # Band 1: Red, Band 2: Green, Band 3: Blue
    r = np.zeros((height, width), dtype=np.uint8)
    g = np.zeros((height, width), dtype=np.uint8)
    b = np.zeros((height, width), dtype=np.uint8)

    # 1. Agricultural / Forest green areas
    g[:, :] = 120
    r[:, :] = 60
    b[:, :] = 40

    # 2. Water body (river / coastal ocean)
    r[300:512, :] = 20
    g[300:512, :] = 70
    b[300:512, :] = 180

    # 3. Urban buildings & roads (grey / bright rooftops)
    r[50:200, 100:350] = 190
    g[50:200, 100:350] = 180
    b[50:200, 100:350] = 175

    # Road network (straight lines)
    r[120:135, :] = 80
    g[120:135, :] = 80
    b[120:135, :] = 80

    r[:, 220:235] = 80
    g[:, 220:235] = 80
    b[:, 220:235] = 80

    transform = from_origin(77.5946, 12.9716, 0.0001, 0.0001)
    
    with rasterio.open(
        filename,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=3,
        dtype='uint8',
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)

    print(f"Created high-resolution synthetic satellite raster: {filename}")

if __name__ == "__main__":
    create_sample_geotiff("demo_satellite.tif")
    create_sample_geotiff("test1.tif")
