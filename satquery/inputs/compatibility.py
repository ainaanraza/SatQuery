def check_spatial_compatibility(image_a, image_b):
    return {
        "same_crs": image_a.crs == image_b.crs,
        "overlap": True,
        "resolution_compatible": image_a.resolution_x == image_b.resolution_x,
        "grid_aligned": False,
        "requires_reprojection": image_a.crs != image_b.crs,
        "requires_resampling": image_a.resolution_x != image_b.resolution_x
    }
