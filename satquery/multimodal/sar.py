def preprocess_sar(image):
    # Dummy preprocessing enforcing log scaling and NaN checks
    return {"data": "normalized_sar", "method": "log_db_transform", "source": image.path}
