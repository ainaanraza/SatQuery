# SatQuery AI Phase 5 Implementation

## Multimodal Architecture
Introduces `satquery/multimodal` packaging distinct SAR and Optical preprocessing algorithms safely feeding into a deterministic `OpticalSARFusionTool`. Registration strategies enforce EPSG grid safety before stacking variables.

## Semantic Interpretation
Separates observed pixel differences from inferential semantic claims via `SemanticChangeInterpreter`. Hard-enforces hallucination protections returning `UNKNOWN_CHANGE` unless explicit model metrics are configured in the pipeline.

## Evidence Graph
Expands provenance from linear `ToolResult` attachments to a hierarchical graph connecting Source -> Preprocessing -> Detection -> Tracking -> Interpretation.
