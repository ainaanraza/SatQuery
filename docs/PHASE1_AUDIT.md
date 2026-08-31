# Repository Audit for SatQuery Phase 1

## Repository structure
```
d:\satquery\GeoChat
├── README.md
├── demo_images/
├── docs/
├── geochat/
├── geochat_demo.py
├── images/
├── playground/
├── pyproject.toml
└── scripts/
```

## Python packages
The main package is currently named `geochat`, containing:
- `eval/`
- `model/`
- `serve/`
- `train/`

## Entry points
- `geochat_demo.py`
- `geochat/serve/gradio_web_server.py`
- `geochat/eval/batch_geochat_*.py`
- `geochat/train/train.py`

## Inference flow
Inference is handled mainly through `geochat_demo.py`, utilizing `geochat.model.builder` and `geochat.conversation`. The model consumes image tensors directly via `mm_utils`.

## Image preprocessing flow
Images are currently processed using standard vision-language pre-processors (e.g. CLIP image processor) via `mm_utils.py` and potentially huggingface `transformers` features. No robust geospatial preprocessing exists.

## Configuration files
- `pyproject.toml`
- `scripts/zero2.json`, `zero3.json`, etc.

## Training flow
Handled via bash scripts in `scripts/` (e.g., `finetune_lora.sh`, `finetune_full_schedule.sh`) calling into `geochat/train/train.py` and `geochat_trainer.py`.

## Evaluation flow
Handled by scripts in `geochat/eval/` (e.g., `batch_geochat_vqa.py`, `batch_geochat_grounding.py`).

## Branding references
Branding references found across:
- `README.md`
- `pyproject.toml`
- `geochat_demo.py`
- Package names (`geochat/`)
- Module names (e.g., `geochat_arch.py`, `geochat_trainer.py`, `batch_geochat_*.py`)
- Documentation in `docs/`
- Shell scripts in `scripts/`
- Deep inside source files in imports, comments, string literals, exception texts.

## Potential rename conflicts
- Third-party model names like `Llama`, `CLIP`, `Vicuna` should be preserved.
- If dependencies use `GeoChat` for pretrained weights from HuggingFace, URLs and model identifiers might need to be kept as attribution or carefully ported/documented. 

## Potential breaking changes
- Renaming the package from `geochat` to `satquery` will break any external tools referencing this package if compatibility aliases aren't provided.
- Renaming model classes (`GeoChatLlamaForCausalLM` -> `SatQueryLlamaForCausalLM`) could break loading of old checkpoint states if state dicts have hardcoded class names (though typically standard HuggingFace handles this gracefully via architectures).

## Phase 1 implementation plan
1. Perform package structure rename (`geochat` -> `satquery`).
2. Rename module files and entry point scripts (e.g., `geochat_demo.py` -> `satquery_demo.py`).
3. Mass update of text, replacing `GeoChat`, `geochat`, etc. with `SatQuery`, `satquery`, while ensuring safe casing.
4. Rewrite `README.md` and `docs/` content for SatQuery AI.
5. Create `satquery/inputs/` directory.
6. Implement `RSImage`, `RasterLoader` (using `rasterio`), metadata extraction, modality/sensor detection, tiling basics, and validation logic.
7. Create a basic CLI for raster inspection `python -m satquery.inspect`.
8. Write comprehensive unit tests in `tests/`.
9. Run regression evaluation to ensure original model functionality is preserved.
10. Finalize branding search to ensure no leftover references.
