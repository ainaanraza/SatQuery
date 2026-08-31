from .registry import ModelRegistry

class ModelManager:
    _instance = None
    _provider = None

    @classmethod
    def get_provider(cls, provider_name="mock"):
        if cls._provider is None:
            cls._provider = ModelRegistry.get_provider(provider_name)
            cls._provider.load()
        return cls._provider
