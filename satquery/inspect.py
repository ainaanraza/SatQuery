import argparse
from .inputs import load_raster, validate_image

def main():
    parser = argparse.ArgumentParser(description="SatQuery AI - Raster Inspector")
    parser.add_argument("path", help="Path to raster file")
    args = parser.parse_args()
    
    try:
        img = load_raster(args.path)
        val = validate_image(img)
        
        print("SatQuery AI — Raster Inspector\n")
        print(f"File: {img.path}")
        print(f"Width: {img.width}")
        print(f"Height: {img.height}")
        print(f"Bands: {img.band_count}")
        print(f"CRS: {img.crs}")
        print(f"Resolution: {img.resolution_x} x {img.resolution_y}")
        print(f"Bounds: {img.bounds}")
        print(f"Sensor: {img.sensor}")
        print(f"Modality: {img.modality}")
        print(f"Acquisition Time: {img.acquisition_time}")
        print(f"NoData: {img.nodata}\n")
        
        print("Validation:")
        print(f"{'✓' if val.checks.get('file_readable') else '✗'} File readable")
        print(f"{'✓' if val.checks.get('raster_valid') else '✗'} Raster valid")
        print(f"{'✓' if val.checks.get('crs_available') else '⚠'} CRS available")
        print(f"{'✓' if val.checks.get('bounds_valid') else '⚠'} Bounds valid")
        if img.acquisition_time is None:
            print("⚠ Acquisition time unavailable")
    except Exception as e:
        print(f"SatQuery could not open the input file. Error: {e}")

if __name__ == "__main__":
    main()
