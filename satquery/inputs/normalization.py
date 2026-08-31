import numpy as np

def normalize_array(array, method="percentile", lower_percentile=2, upper_percentile=98):
    if not isinstance(array, np.ndarray):
        raise TypeError("Input must be a NumPy array.")
    
    array = array.astype(np.float32)
    # Handle NaN explicitly
    valid_mask = ~np.isnan(array)
    if not np.any(valid_mask):
        return array, {"method": method, "status": "all_nan"}
    
    valid_data = array[valid_mask]
    metadata = {"method": method}
    
    if method == "minmax":
        dmin = np.min(valid_data)
        dmax = np.max(valid_data)
        if dmax > dmin:
            array[valid_mask] = (array[valid_mask] - dmin) / (dmax - dmin)
        else:
            array[valid_mask] = 0.0
        metadata.update({"min": dmin, "max": dmax})
        
    elif method == "percentile":
        p_low = np.percentile(valid_data, lower_percentile)
        p_high = np.percentile(valid_data, upper_percentile)
        
        if p_high > p_low:
            array[valid_mask] = np.clip((array[valid_mask] - p_low) / (p_high - p_low), 0, 1)
        else:
            array[valid_mask] = 0.0
            
        metadata.update({"p_low": p_low, "p_high": p_high})
        
    elif method == "standard":
        mean = np.mean(valid_data)
        std = np.std(valid_data)
        if std > 0:
            array[valid_mask] = (array[valid_mask] - mean) / std
        else:
            array[valid_mask] = 0.0
        metadata.update({"mean": mean, "std": std})
    else:
        raise ValueError(f"Unknown normalization method: {method}")

    return array, metadata
