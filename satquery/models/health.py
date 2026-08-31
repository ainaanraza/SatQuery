def get_model_health(provider, model_name):
    return {
        "provider": provider,
        "model": model_name,
        "version": "1.0",
        "device": "cpu",
        "dtype": "float32",
        "loaded": True,
        "available": True,
        "memory_estimate": "100MB",
        "status": "READY"
    }
