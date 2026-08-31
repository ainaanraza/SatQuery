from typing import List
from satquery.inputs.models import RSImage
from satquery.inputs.raster_loader import load_raster

class InputResolver:
    def resolve(self, inputs: List[str]) -> List[RSImage]:
        resolved = []
        for inp in inputs:
            try:
                # Assume inp is a path
                resolved.append(load_raster(inp))
            except Exception:
                pass
        return resolved
