from .state import AgentState
from .parser import QueryUnderstandingBackend
from .intent import Intent
from .resolver import InputResolver
from .planner import Planner
from .executor import Executor
from .synthesizer import Synthesizer
from satquery.inputs.exceptions import SatQueryInputError
from satquery.tools import get_default_registry

class SatQueryAgent:
    def __init__(self):
        self.registry = get_default_registry()
        self.parser = QueryUnderstandingBackend()
        self.resolver = InputResolver()
        self.planner = Planner(self.registry)
        self.executor = Executor(self.registry)
        self.synthesizer = Synthesizer()

    def run(self, query: str, inputs: list):
        state = AgentState(query=query)

        state.parsed_query = self.parser.parse(query)
        state.intent = Intent(name=state.parsed_query.operation, confidence=1.0)

        # Inputs may be paths (resolved to RSImage here) or RSImage objects.
        # Unloadable paths are reported as errors rather than silently dropped.
        resolved_inputs = []
        for i in inputs:
            if isinstance(i, str):
                try:
                    resolved_inputs.extend(self.resolver.resolve([i]))
                except SatQueryInputError as e:
                    state.errors.append(str(e))
            else:
                resolved_inputs.append(i)

        state.inputs = resolved_inputs

        required = len(state.parsed_query.required_inputs)
        if not state.errors and len(state.inputs) < required:
            state.errors.append(
                f"Operation '{state.parsed_query.operation}' requires {required} input image(s), "
                f"but {len(state.inputs)} were provided."
            )

        if not state.errors:
            self.planner.generate_plan(state)
            if self.planner.validate_plan(state):
                self.executor.execute(state)

        response = self.synthesizer.synthesize(state)
        return response
