from .providers.mock import MockProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.hf_llava import HuggingFaceLLaVAProvider

class ModelRegistry:
    providers = {
        "mock": MockProvider,
        "huggingface": HuggingFaceProvider,
        "hf_llava": HuggingFaceLLaVAProvider
    }
    
    @classmethod
    def get_provider(cls, name):
        return cls.providers.get(name, MockProvider)()
