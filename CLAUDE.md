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
4. `agent/executor.py`: runs the calls in order and merges each `ToolResult`'s evidence, errors, and warnings into the state. Tools can't pass outputs to each other except through `context` (the `AgentState`).
5. `agent/synthesizer.py`: the answer comes from the last `vision.answer` result, otherwise from `raster.metadata`. Confidence is hard-coded to 0.9.

Tools: subclass `SatQueryTool` (`tools/base.py`), set `name`, and implement `execute(context, arguments) -> ToolResult`. Register new tools in `tools/__init__.py::get_default_registry`, then reference them from the planner.

Models: `tools/model.py` (`vision.answer`) → `models/manager.py::ModelManager` (a process-wide singleton that caches the **first** provider loaded) → `models/registry.py`. Unknown provider names fall back to `MockProvider` without any warning. Providers implement `MultimodalModelProvider.infer(ModelInferenceRequest) -> ModelInferenceResult` and put text in `predictions["text"]`.

Evidence: each tool should emit `evidence.models.Evidence` records (source, tool, bounds/CRS/transform, confidence). `evidence/graph.py::EvidenceGraph` exists but the agent doesn't use it.

Frontend: static `satquery/frontend/` (open `index.html` directly). The API URL is hard-coded on line 1 of `app.js` (`API_BASE_URL`).

## Known placeholders / incomplete areas

The README describes more than the code currently does. Check the code before trusting a feature description.

- Change pipeline uses fake data: `change_detection` returns default counts (1500/10000) and `mask: "computed_mask_placeholder"`, `change_localization` returns constant area/bounds, and the planner passes literals (`"computed_mask"`, `change_percentage: 15.0`) instead of real upstream outputs.
- `MockProvider` returns `{"category": ...}` with no `"text"`, so `vision.answer` falls back to the string `"Analyzed {question} on satellite raster."`. The tests depend on that fallback.
- Many packages are stubs or not connected to the agent: `semantic/`, `geospatial/`, `confidence/`, `storage/`, `datasets/`, `reproducibility/`, `performance/`, `visualization/`, `evaluation/` (only the benchmark CLI), `models/{health,lifecycle,hashing}.py`, `models/providers/huggingface.py`, `config/{development,production}.py`. `reasoning/` is used only by `tools/reasoning.py`, which isn't registered.
- `docs/*.md` (PRODUCTION_*, OPERATIONS_RUNBOOK, etc.) mostly describe aspirational "phase" designs, not the current implementation. `docker-compose.yml` declares postgres/redis services that nothing uses.

## Legacy GeoChat code

`satquery/model/` (LLaVA/MPT architecture), `train/`, `serve/` (Gradio + controller/worker), `eval/batch_satquery_*.py`, `conversation.py`, `mm_utils.py`, `utils.py`, `scripts/*.sh` (DeepSpeed fine-tuning), and `playground/` all come from the original GeoChat training/serving stack. They pin old dependencies (`torch==2.0.1`, `transformers==4.31.0`) and are independent of the agent pipeline. Don't confuse `satquery/model/` (legacy) with `satquery/models/` (the active provider layer).

## Worklog

`WORKLOG.md` tracks completed work. After finishing a feature, fix, or notable change, add an entry at the top using the format given in that file (what, why, short notes, branch/commit).

## Repo hygiene

`.gitignore` excludes bytecode, `*.egg-info/`, venvs, caches, `.env*`, and model weights. The sample rasters (`test1.tif`, `test2.tif`, `demo_satellite.tif`) are intentionally tracked.
