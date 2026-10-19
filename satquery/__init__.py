def __getattr__(name):
    # The legacy GeoChat model imports torch/transformers; load it only when it is actually requested,
    # so the agent, API, and CLI start without that cost.
    if name == "SatQueryLlamaForCausalLM":
        from .model import SatQueryLlamaForCausalLM
        return SatQueryLlamaForCausalLM
    raise AttributeError(f"module 'satquery' has no attribute {name!r}")
