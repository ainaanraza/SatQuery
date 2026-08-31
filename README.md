# SatQuery AI

SatQuery AI is an advanced agentic remote-sensing and geospatial intelligence system. It transitions from basic vision-language models into an autonomous agent pipeline capable of deeply analyzing satellite imagery across multiple modalities, resolutions, and temporal epochs.

## Architecture

SatQuery AI currently implements a phased intelligence pipeline:

- **Phase 1: Geospatial Input Foundation.** Memory-safe loading and tiling of GeoTIFFs utilizing `rasterio` abstractions.
- **Phase 2: Agentic Orchestration.** Capability-driven dynamic planners, intent parsers, and tool executors seamlessly routing queries through a resilient N-step task tree mapping directly to real geospatial artifacts.
- **Phase 3: Analytical Intelligence.** Robust tool-sets enabling CRS-aware Spatial Alignment, Change Detection, Localization, and deterministic Optical/SAR Fusion.
- **Phase 4: Temporal Intelligence.** An advanced `TemporalSeries` integration facilitating multi-image sequence generation, deterministic ordering, persistent region identity tracking, and trend analysis across chronologically aligned time-series arrays.

## Key Capabilities
- Memory-safe Large Raster parsing via windowed chunking.
- End-to-end evidence tracking binding text-synthesis directly to exact raster coordinates.
- Cross-modal analysis validating SAR alongside Optical grids.

## Setup
```bash
pip install -e .
```

## Usage
Interact through the CLI:
```bash
python -m satquery.agent_cli --images image1.tif image2.tif --query "What changed between these images?"
```

## Disclaimer
SatQuery AI handles deterministic geomathematical analytics natively but relies on validated model stubs for high-level semantic labeling absent configured checkpoint weights.
