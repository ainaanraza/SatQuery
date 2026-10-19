import os
from .registry import ModelRegistry

class ModelManager:
    # One loaded provider instance per provider name, shared process-wide.
    _providers = {}

    @classmethod
    def get_provider(cls, provider_name=None):
        if provider_name is None:
            provider_name = os.environ.get("SATQUERY_MODEL_PROVIDER", "mock")
        if provider_name not in cls._providers:
            provider = ModelRegistry.get_provider(provider_name)
            provider.load()
            cls._providers[provider_name] = provider
        return cls._providers[provider_name]
