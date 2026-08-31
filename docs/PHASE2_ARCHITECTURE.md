# SatQuery AI Phase 2 Architecture

The architecture builds on Phase 1 (`satquery.inputs`) introducing an Agentic Orchestration layer.

## Architecture Diagram

```
User Query -> Parser -> Intent -> Resolver -> Planner -> Tools (Metadata, Raster, Vision) -> Evidence Collector -> Synthesizer -> Grounded Response
```

## State & Models

- `AgentState`: maintains the execution context (intent, tools, evidence, results, plan).
- `SatQueryTool`: base contract containing inputs/outputs and `ToolCapabilities`.
- `ToolRegistry`: registry pattern for discovery of capabilities without hardcoded conditionals.
- `Evidence`: records source, geographic properties, confidence, and tools executed to answer provenance.

## Execution
Tools execute natively within `Executor`, driven by a generated `Plan`. The `Synthesizer` correlates tool `results` and `evidence` lists into a single structured user output.
