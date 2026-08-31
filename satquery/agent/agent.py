from .state import AgentState
from .parser import QueryUnderstandingBackend
from .intent import Intent
from .resolver import InputResolver
from .planner import Planner
from .executor import Executor
from .synthesizer import Synthesizer
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
        
        # In a real scenario, inputs might be paths or RSImage objects.
        # If they are strings, we resolve them.
        resolved_inputs = []
        for i in inputs:
            if isinstance(i, str):
                resolved = self.resolver.resolve([i])
                resolved_inputs.extend(resolved)
            else:
                resolved_inputs.append(i)
                
        state.inputs = resolved_inputs
        
        self.planner.generate_plan(state)
        
        if self.planner.validate_plan(state):
            self.executor.execute(state)
            
        response = self.synthesizer.synthesize(state)
        return response
