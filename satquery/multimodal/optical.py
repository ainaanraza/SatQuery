def preprocess_optical(image):
    # Dummy preprocessing enforcing normalization limits
    return {"data": "normalized_optical", "method": "percentile_stretch", "source": image.path}
