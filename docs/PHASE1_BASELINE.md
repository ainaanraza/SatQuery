# SatQuery AI Phase 1 Baseline

Model: GeoChat
Checkpoint: Not loaded locally yet (requires downloading weights)
Python version: 3.8+
Inference command: python geochat_demo.py
VQA status: Unknown (assumed functional prior to rename)
Captioning status: Unknown (assumed functional prior to rename)
Grounding status: Unknown (assumed functional prior to rename)
Checkpoint loading status: Assumed working

Note: This baseline is captured before rename. The model uses Hugging Face AutoConfig.register('geochat', GeoChatConfig) which embeds 'geochat' model_type in the config.json of checkpoints. When we rename the class to SatQueryConfig, we MUST register it with both 'geochat' and 'satquery' model_types or handle compatibility in builder.py so old checkpoints load.
