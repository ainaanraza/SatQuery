# Worklog

Running log of changes on SatQuery AI: what was done, why, and a short description. Newest entries first.

Entry format:

```
## YYYY-MM-DD — Short title
**Branch:** <branch> · **Commit:** <sha>
**What:** what changed (files/modules touched).
**Why:** the problem or goal behind it.
**Notes:** behaviour, usage, limitations, follow-ups (optional).
```

---

## 2026-10-19 — Acquisition dates, honest benchmark scoring, small fixes
**Branch:** `feature/enhancements-and-completion`
**What:**
- **Acquisition dates** (`inputs/metadata.py`, `inputs/raster_loader.py`, `inputs/models.py`): `load_raster` now fills `acquisition_time`. It checks explicit acquisition tags first (`ACQUISITION_DATE`, `DATE_ACQUIRED`, `SENSING_TIME`, `PRODUCT_START_TIME`, …), then Sentinel/Landsat-style filename dates, then `TIFFTAG_DATETIME`. Timezone-aware values are converted to naive UTC so they can be compared. The new `RSImage.acquisition_time_source` records which source was used.
- **Temporal alignment** (`tools/temporal_alignment.py`): warns when inputs arrive in reverse chronological order, or when a date came from the filename or `TIFFTAG_DATETIME`. Reports `before_path`/`after_path`.
- **Benchmark** (`evaluation/benchmark.py`, `evaluation/metrics.py`):
  - Removed the 75% score floor and the fabricated "concept coverage" (accuracy + 4.2).
  - Removed the invented ground truth ("harbor, vessels, …") for unlabeled samples, and the silent `test1.tif` fallback for missing images.
  - The loader now resolves VRSBench `image_id` references (previously ignored, so samples were scored against `test1.tif`), handles caption records, and counts skipped samples by reason.
  - Reports `exact_match`, `contains_match`, `token_f1`, and `bleu_1`, overall and per question type, with the real model id. Added an `--output` flag.
  - The `iou` metric was a stub returning 0; it is now a real box IoU.
- **README**: withdrew the 75.00% / 79.20% figures pending re-evaluation, documented the metrics, and corrected the RSVQA/CDVQA claims (the native formats are not parsed yet).
- **Parser** (`agent/parser.py`): whole-word keyword matching ("necessary" no longer triggers SAR fusion, "exchange" no longer triggers change analysis); also accepts "radar" and "multispectral".
- **Models** (`models/manager.py`, `models/registry.py`): one cached instance per provider name instead of a single global one that ignored later requests. An unknown provider name now logs a warning.
- Tests: 14 new tests (date parsing and sources, end-to-end reverse-order dates, parser, model manager, metrics, benchmark loader and scoring). Suite total: 38.

**Why:** The temporal half of change analysis could never work without dates. The README's headline benchmark numbers came from the scorer's floor and fabricated coverage, not from model quality, and VRSBench samples weren't even evaluated on their own images. For an evaluated submission, invalid metrics are a bigger risk than missing ones.

**Notes:** Valid benchmark numbers need a GPU re-run (`python -m satquery.evaluation.benchmark --dataset <VRSBench> --provider hf_llava`). Native RSVQA/CDVQA loaders remain to be done.

## 2026-10-19 — Real change detection pipeline and honest failure handling
**Branch:** `feature/enhancements-and-completion` · **Commit:** `c83b7c2a`
**What:**
- `tools/change_detection.py`: computes real pixel-level change over the spatial overlap of two rasters (area-averaged onto image A's grid, capped at 2048 px per side). It ignores nodata/NaN pixels, scales each band's difference by its joint 2–98 percentile span, takes the mean across bands, and applies a threshold (default 0.15). Returns the boolean mask, its geotransform, and the CRS. The existing count-based path and its input validation are kept.
- `tools/change_localization.py`: groups the change mask into 4-connected regions (pure-numpy BFS on a ≤64×64 cell grid, so no scipy dependency). Reports geographic bounds and m² area per region and overall (exact for projected CRS, equirectangular approximation for geographic CRS).
- `tools/change_summary.py`: builds the answer from the real statistics, area, regions, and acquisition order.
- `agent/state.py` + `agent/executor.py`: new `ResultRef` placeholders pass earlier tools' outputs to later ones. The executor stops at the first failed tool or exception.
- `tools/spatial_alignment.py`: fails on CRS mismatch or no overlap. A resolution mismatch is only a warning, since the pair is resampled.
- `agent/resolver.py` + `agent/agent.py`: missing or unreadable inputs, and too few images for the operation, become errors instead of being silently dropped.
- `agent/synthesizer.py`: answers change queries from `change_summary`. Warnings appear as limitations, and confidence comes from model evidence instead of a hard-coded 0.9.
- `tools/model.py`, `models/providers/mock.py`, `models/providers/hf_llava.py`: removed fabricated answers. There is no more `"Analyzed ... on satellite raster"` fallback and no green dummy image when the input is missing. The mock provider labels its output as mock.
- Tests: `tests/tools/test_change_pipeline.py` (11 tests on synthetic GeoTIFFs with known change), plus the earlier `change_detection` input-validation tests.

**Why:** The change-analysis pipeline returned constant placeholder numbers (15%, 50,000 m²), and the agent then answered "no relevant tool provided a synthesis output". Incompatible image pairs were still "analyzed", and missing files produced invented answers. All of this contradicted the project's evidence-grounded, no-hallucination claim.

**Notes:**
- Verified behavior: an identical pair (`test1.tif`/`demo_satellite.tif`) gives 0% change; a synthetic 20×20 px change gives exactly 4.0% and 40,000 m²; the non-overlapping pair (`test1.tif`/`test2.tif`) is refused with a reason.
- Not handled yet: reprojection between CRSs, radiometric normalization across sensors or seasons, and reading acquisition dates (so temporal order is always "unknown").

## 2026-10-19 — Repository hygiene: .gitignore and untracking generated files
**Branch:** `feature/enhancements-and-completion` · **Commit:** `105dbece`
**What:** Added `.gitignore` (Python bytecode, `*.egg-info/`, virtualenvs, test/tool caches, editor/OS files, `.env*`, model weights/checkpoints, `benchmark_results.json`). Removed the tracked `__pycache__/*.pyc` and `satquery.egg-info/` files from the index; they remain on disk.
**Why:** Any run of the code regenerated these files and filled `git status` with ~137 spurious modifications, which hid the real changes.
**Notes:** `test1.tif`, `test2.tif`, and `demo_satellite.tif` are deliberately still tracked because the README and CLI examples use them.

## 2026-10-19 — CLAUDE.md
**Branch:** `feature/enhancements-and-completion` · **Commit:** `105dbece`
**What:** Added `CLAUDE.md` with dev commands (install, tests, CLI, API, benchmark), the agent pipeline architecture (parser → resolver → planner → executor → synthesizer), the tool/model provider extension points, and a list of known placeholders and incomplete modules.
**Why:** Gives future contributors and AI assistants an accurate picture of the code. The README describes several capabilities that are not implemented yet.
**Notes:** The "Known placeholders / incomplete areas" section is the starting backlog for this branch.

## 2026-10-19 — Feature branch created
**Branch:** `feature/enhancements-and-completion` (from `main` @ `1ac4760`)
**What:** Created the working branch for new features, improvements to existing implementations, and completing stubbed modules.
**Why:** Keeps this work isolated from `main` until it is reviewed.
