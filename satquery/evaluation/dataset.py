import json

class DatasetManifest:
    def __init__(self, path):
        self.path = path
    def load(self):
        return []
    def check_leakage(self, splits):
        return {"leakage_detected": False}
