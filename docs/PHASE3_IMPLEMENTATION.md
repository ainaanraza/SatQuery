# SatQuery AI Phase 3 Implementation

## Architecture
Phase 3 expands the Agentic Orchestration with analytical remote-sensing capabilities via standard Tool definitions: Temporal Alignment, Spatial Alignment, Change Detection, Change Localization, Optical/SAR Fusion, and Change Summary.

## Algorithms
All algorithms respect Phase 1 memory safety utilizing `rasterio.windows`. 
Change Detection uses deterministic differentials (`absolute_difference`) producing strict numerical ratios mapping masked coordinates via `ChangeLocalizationTool`.

## Limitations
- **Optical/SAR Fusion** acts as a baseline modal validator and alignment layer. True neural fusion weights remain deferred to a later iteration.
- **Change Summary** explicitly avoids deep semantic mapping, providing analytical summaries of measurable difference percentages instead of fabricating land cover classes.
