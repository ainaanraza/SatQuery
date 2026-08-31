from transformers import AutoConfig

def enable_legacy_checkpointing():
    # Only import these when explicitly needed
    from satquery.model.language_model.satquery_llama import SatQueryConfig
    from satquery.model.language_model.satquery_mpt import SatQueryMPTConfig
    
    # Register old geochat model types for loading legacy HF checkpoints
    AutoConfig.register("geochat", SatQueryConfig)
    AutoConfig.register("geochat_mpt", SatQueryMPTConfig)
