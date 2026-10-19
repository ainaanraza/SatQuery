from satquery.models.manager import ModelManager
from satquery.models.providers.mock import MockProvider

def test_providers_cached_per_name():
    mock = ModelManager.get_provider("mock")
    assert ModelManager.get_provider("mock") is mock
    assert ModelManager.get_provider("huggingface") is not mock

def test_unknown_provider_warns_and_falls_back(caplog):
    with caplog.at_level("WARNING"):
        provider = ModelManager.get_provider("does-not-exist")
    assert isinstance(provider, MockProvider)
    assert "Unknown model provider 'does-not-exist'" in caplog.text
