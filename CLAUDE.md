# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SatQuery AI: an agentic remote-sensing Q&A system (ISRO AI Hackathon). A natural-language query plus one or more GeoTIFFs goes through a rule-based agent pipeline that calls analytical tools and optionally a VLM (RS-LLaVA-1.5-7B, 4-bit). The repo is a fork of GeoChat (MBZUAI), and the original GeoChat code is still present (see "Legacy code" below).

## Commands

A local venv is at `.venv/` (Windows: `.venv/Scripts/python.exe`).

```bash
pip install -e .                        # pyproject.toml; rasterio is NOT listed there and must be installed separately
python -m pytest -q tests               # full suite (fast, CPU-only, uses mock model provider)
python -m pytest tests/agent/test_agent.py::test_agent_vqa   # single test
python -m satquery.agent_cli --query "..." --image test1.tif
python -m satquery.agent_cli --query "Detect change" --image-before demo_satellite.tif --image-after test1.tif
uvicorn satquery.api.app:app --host 0.0.0.0 --port 8000      # REST API (also the Docker CMD)
python -m satquery.evaluation.benchmark --dataset <path> --provider hf_llava --samples 20
python -m satquery.create_demo_raster   # generate synthetic GeoTIFFs
```

There is no linter/formatter config and no CI.

Environment variables: `SATQUERY_MODEL_PROVIDER` (`mock` default | `huggingface` | `hf_llava`), `SATQUERY_ENV`, `SATQUERY_DEVICE`. `hf_llava` needs a GPU and downloads `llava-hf/llava-1.5-7b-hf` + the `BigData-KSU/RS-llava-v1.5-7b-LoRA` adapter.

## Architecture (active code path)

Request flow: `api/app.py` (`POST /analyze`) → `jobs/manager.py` (in-memory dict; runs the job synchronously despite returning `"queued"`) → `agent/agent.py::SatQueryAgent.run`, which fills one `AgentState` (`agent/state.py`) through these stages:

1. `agent/parser.py`: keyword matching picks an `operation`: `image_question_answering`, `change_analysis` ("change/before/after/difference"), `optical_sar_fusion` ("sar" and "optical"), or `metadata_query`.
2. `agent/resolver.py`: turns string paths into `RSImage` (`inputs/models.py`) via `inputs/raster_loader.py` (rasterio). It also tries Colab paths (`/content/GeoChat`, `/content/data/VRSBench`), and images that fail to load are **silently dropped**.
3. `agent/planner.py`: a hard-coded `if/elif` on operation produces a list of `ToolCall(tool_name, arguments)`. Tool names must match keys in the registry.
4. `agent/executor.py`: runs the calls in order and merges each `ToolResult`'s evidence, errors, and warnings into the state. It **stops at the first failed tool**. Planner arguments can be `ResultRef(tool_name, key)` placeholders, which the executor replaces with that field of an earlier tool's `data`. This is how real outputs flow between steps, e.g. `change_detection`'s mask goes to `change_localization`.
5. `agent/synthesizer.py`: the answer comes from `vision.answer`, then `change_summary`, then `optical_sar_fusion`, then `raster.metadata`, or becomes an error message if `state.errors` is non-empty. Tool warnings become `limitations`. `confidence` is the minimum of the model-derived evidence confidences, or `None` if no model was involved.

Acquisition dates (`inputs/metadata.py::detect_acquisition_time`) are looked up in this order: explicit acquisition tags, then a date in a Sentinel/Landsat-style filename, then `TIFFTAG_DATETIME` as a last resort (often the processing date). `RSImage.acquisition_time_source` records which one was used, and `temporal_alignment` turns non-tag sources into warnings.

Unloadable inputs and too few images for the operation are recorded as errors before planning starts. Nothing is silently dropped.

Change pipeline: `change_detection` reads the overlap of both rasters onto image A's grid (area-averaged, capped at `max_size` px per side). It scores each pixel by the mean, across bands, of the absolute difference divided by that band's 2nd-98th percentile span, then thresholds the score (default 0.15). `change_localization` groups the resulting mask into connected regions (pure-numpy BFS on a coarse grid; there is no scipy dependency) and computes the area in m². `spatial_alignment` fails the plan on a CRS mismatch or no overlap.

Shared co-registration lives in `multimodal/registration.py` (`common_grid`, `read_on_grid`). Both change detection and fusion use it; use it for any new tool that compares two rasters.

Optical-SAR fusion (`tools/optical_sar_fusion.py` + `multimodal/`) maps water:
- **SAR:** below −18 dB if the data is calibrated (float dB, or linear power converted to dB); below an Otsu threshold if it is uncalibrated integer DN.
- **Optical:** NDWI > 0, but only when green and NIR bands are identified from band descriptions (B3/B8/green/nir).
- **Output:** each sensor's water fraction, their agreement, and the SAR water regions and area.

The tool works out which input is optical and which is SAR from `RSImage.modality`, which comes from the sensor tag or band names (VV/VH → SAR). If the modality is unknown, it accepts a SAR input only if it has ≤2 bands, and otherwise refuses instead of guessing.

Tools: subclass `SatQueryTool` (`tools/base.py`), set `name`, and implement `execute(context, arguments) -> ToolResult`. Register new tools in `tools/__init__.py::get_default_registry`, then reference them from the planner.

Models: `tools/model.py` (`vision.answer`) → `models/manager.py::ModelManager` (caches one loaded instance per provider name) → `models/registry.py`. Unknown provider names log a warning and fall back to `MockProvider`. `MockProvider` ignores the image and returns `"[mock provider - no vision model loaded] Analyzed question: ..."`. Providers implement `MultimodalModelProvider.infer(ModelInferenceRequest) -> ModelInferenceResult` and put text in `predictions["text"]`.

Evidence: each tool should emit `evidence.models.Evidence` records (source, tool, bounds/CRS/transform, confidence). Keep `Evidence.metadata` JSON-friendly; don't put arrays or `Affine` objects in it.

After synthesis, `agent/provenance.py::build_evidence_graph` builds an `EvidenceGraph` of inputs → tool steps → answer and stores it in `response.evidence_graph`. Edges are derived from the plan: an `RSImage` argument links that input to the step, and a `ResultRef` links the producing step. The answer is linked from the tool named in `response.answer_source`, or from the failing step. New tools get correct graph edges automatically, as long as they receive data through `ResultRef`.

`jobs/manager.py` returns `success`, `answer`, `answer_source`, `confidence`, `errors`, `limitations`, `evidence`, and `evidence_graph`. It passes everything through `visualization/serialization.py::to_jsonable` (datetimes → ISO strings, arrays → shape summaries, Affine → 6-float lists).

Frontend: static `satquery/frontend/` (open `index.html` directly). The API URL is hard-coded on line 1 of `app.js` (`API_BASE_URL`). `renderEvidenceGraph` draws the graph, and `STEP_FACTS` defines the facts shown per tool, so add an entry there for any new tool. Pass all server strings through `escapeHtml`.

## Known placeholders / incomplete areas

The README describes more than the code currently does. Check the code before trusting a feature description.

- The benchmark loader reads VRSBench-style, LLaVA-conversation, and simple Q/A JSON. The native RSVQA and CDVQA layouts (questions and answers in separate files) aren't parsed. No valid benchmark numbers have been published since the inflated scorer was removed.
- Many packages are stubs or not connected to the agent: `semantic/`, `geospatial/`, `confidence/`, `storage/`, `datasets/`, `reproducibility/`, `performance/`, `visualization/`, `evaluation/` (only the benchmark CLI), `models/{health,lifecycle,hashing}.py`, `models/providers/huggingface.py`, `config/{development,production}.py`. `reasoning/` is used only by `tools/reasoning.py`, which isn't registered.
- `docs/*.md` (PRODUCTION_*, OPERATIONS_RUNBOOK, etc.) mostly describe aspirational "phase" designs, not the current implementation. `docker-compose.yml` declares postgres/redis services that nothing uses.

## Legacy GeoChat code

`satquery/model/` (LLaVA/MPT architecture), `train/`, `serve/` (Gradio + controller/worker), `eval/batch_satquery_*.py`, `conversation.py`, `mm_utils.py`, `utils.py`, `scripts/*.sh` (DeepSpeed fine-tuning), and `playground/` all come from the original GeoChat training/serving stack. They pin old dependencies (`torch==2.0.1`, `transformers==4.31.0`) and are independent of the agent pipeline. Don't confuse `satquery/model/` (legacy) with `satquery/models/` (the active provider layer).

## Worklog

`WORKLOG.md` tracks completed work. After finishing a feature, fix, or notable change, add an entry at the top using the format given in that file (what, why, short notes, branch/commit).

## Repo hygiene

`.gitignore` excludes bytecode, `*.egg-info/`, venvs, caches, `.env*`, and model weights. The sample rasters (`test1.tif`, `test2.tif`, `demo_satellite.tif`) are intentionally tracked.
