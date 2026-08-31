import hashlib
import json

def hash_inference(input_data, config):
    hasher = hashlib.sha256()
    hasher.update(str(input_data).encode())
    hasher.update(json.dumps(config, sort_keys=True).encode())
    return hasher.hexdigest()
