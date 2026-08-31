from .providers.mock import MockProvider
from .providers.huggingface import HuggingFaceProvider

class ModelRegistry:
    providers = {
        "mock": MockProvider,
        "huggingface": HuggingFaceProvider
    }
    
    @classmethod
    def get_provider(cls, name):
        return cls.providers.get(name, MockProvider)()
