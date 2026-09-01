import os
from .registry import ModelRegistry

class ModelManager:
    _instance = None
    _provider = None

    @classmethod
    def get_provider(cls, provider_name=None):
        if provider_name is None:
            provider_name = os.environ.get("SATQUERY_MODEL_PROVIDER", "mock")
        if cls._provider is None:
            cls._provider = ModelRegistry.get_provider(provider_name)
            cls._provider.load()
        return cls._provider
