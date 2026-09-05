from .state import AgentState
from satquery.tools.registry import ToolRegistry


class Executor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, state: AgentState):
        for call in state.plan:
            tool = self.registry.get(call.tool_name)

            if not tool:
                continue

            # Do not run change detection if spatial alignment failed.
            if call.tool_name == "change_detection":
                for previous_result in reversed(state.results):
                    if previous_result.tool_name == "spatial_alignment":
                        if not previous_result.success:
                            state.errors.append(
                                "Change detection skipped because spatial alignment failed."
                            )
                            return
                        break

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

            # Pass the actual change percentage produced by change detection
            # to the summary tool.
            if call.tool_name == "change_summary":
                for previous_result in reversed(state.results):
                    if (
                        previous_result.tool_name == "change_detection"
                        and previous_result.success
                        and previous_result.data
                    ):
                        arguments["statistics"] = {
                            "change_percentage": previous_result.data.get(
                                "change_percentage", 0.0
                            )
                        }
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