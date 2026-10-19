from .state import AgentState, ResultRef
from satquery.tools.registry import ToolRegistry

class Executor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, state: AgentState):
        # Tools run in plan order; the first failure stops the plan, since later
        # steps depend on earlier outputs and must not run on missing data.
        for call in state.plan:
            tool = self.registry.get(call.tool_name)
            if not tool:
                continue
            try:
                arguments = self._resolve_arguments(state, call.arguments)
            except LookupError as e:
                state.errors.append(f"{call.tool_name}: {e}")
                break

            try:
                result = tool.execute(context=state, arguments=arguments)
            except Exception as e:
                state.errors.append(f"{call.tool_name} raised {type(e).__name__}: {e}")
                break

            state.results.append(result)
            if result.evidence:
                state.evidence.extend(result.evidence)
            if result.errors:
                state.errors.extend(result.errors)
            if result.warnings:
                state.warnings.extend(result.warnings)
            if not result.success:
                if not result.errors:
                    state.errors.append(f"{call.tool_name} failed.")
                break

    def _resolve_arguments(self, state: AgentState, arguments: dict) -> dict:
        resolved = {}
        for name, value in arguments.items():
            if isinstance(value, dict):
                value = {k: self._resolve_value(state, v) for k, v in value.items()}
            resolved[name] = self._resolve_value(state, value)
        return resolved

    def _resolve_value(self, state: AgentState, value):
        if not isinstance(value, ResultRef):
            return value
        for result in reversed(state.results):
            if result.tool_name == value.tool_name and result.success:
                if value.key is None:
                    return result.data
                if isinstance(result.data, dict) and value.key in result.data:
                    return result.data[value.key]
                raise LookupError(f"'{value.tool_name}' result has no field '{value.key}'")
        raise LookupError(f"no successful '{value.tool_name}' result to read from")
