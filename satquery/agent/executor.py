from .state import AgentState
from satquery.tools.registry import ToolRegistry

class Executor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, state: AgentState):
        for call in state.plan:
            tool = self.registry.get(call.tool_name)
            if tool:
                result = tool.execute(context=state, arguments=call.arguments)
                state.results.append(result)
                if result.evidence:
                    state.evidence.extend(result.evidence)
                if result.errors:
                    state.errors.extend(result.errors)
                if result.warnings:
                    state.warnings.extend(result.warnings)
