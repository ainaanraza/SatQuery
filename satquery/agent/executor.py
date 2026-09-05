from .state import AgentState
from satquery.tools.registry import ToolRegistry


class Executor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, state: AgentState):
        for call in state.plan:
            tool = self.registry.get(call.tool_name)

            if tool:
                arguments = dict(call.arguments)

                # Pass the actual change mask produced by change detection
                # to the localization tool.
                if call.tool_name == "change_localization":
                    for previous_result in reversed(state.results):
                        if (
                            previous_result.tool_name == "change_detection"
                            and previous_result.success
                            and previous_result.data
                        ):
                            arguments["mask"] = previous_result.data.get("mask")
                            break

                result = tool.execute(
                    context=state,
                    arguments=arguments
                )

                state.results.append(result)

                if result.evidence:
                    state.evidence.extend(result.evidence)

                if result.errors:
                    state.errors.extend(result.errors)

                if result.warnings:
                    state.warnings.extend(result.warnings)