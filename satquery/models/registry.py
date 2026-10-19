import logging
from .providers.mock import MockProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.hf_llava import HuggingFaceLLaVAProvider

logger = logging.getLogger(__name__)

class ModelRegistry:
    providers = {
        "mock": MockProvider,
        "huggingface": HuggingFaceProvider,
        "hf_llava": HuggingFaceLLaVAProvider
    }

    @classmethod
    def get_provider(cls, name):
        if name not in cls.providers:
            logger.warning(f"Unknown model provider '{name}'; falling back to the mock provider. "
                           f"Available: {', '.join(cls.providers)}")
        return cls.providers.get(name, MockProvider)()
