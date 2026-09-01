import os
from typing import List
from satquery.inputs.models import RSImage
from satquery.inputs.raster_loader import load_raster

class InputResolver:
    def resolve(self, inputs: List[str]) -> List[RSImage]:
        resolved = []
        for inp in inputs:
            candidate_paths = [
                inp,
                os.path.join(os.getcwd(), inp),
                os.path.join("/content/GeoChat", inp),
                os.path.join("/content/data/VRSBench", inp)
            ]
            loaded = False
            for p in candidate_paths:
                if os.path.exists(p):
                    try:
                        resolved.append(load_raster(p))
                        loaded = True
                        break
                    except Exception:
                        pass
            if not loaded:
                # If still not found, try loading directly with fallback
                try:
                    resolved.append(load_raster(inp))
                except Exception:
                    pass
        return resolved
