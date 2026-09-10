import os
from typing import List, Optional
from satquery.inputs.models import RSImage
from satquery.inputs.raster_loader import load_raster
from satquery.inputs.validator import validate_raster_input

class InputResolver:
    def resolve(self, inputs: List[str], errors: Optional[List[str]] = None) -> List[RSImage]:
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
                    validation = validate_raster_input(p)
                    if not validation.valid:
                        if errors is not None:
                            errors.extend(validation.errors)
                        continue
                    try:
                        resolved.append(load_raster(p))
                        loaded = True
                        break
                    except Exception:
                        pass
            if not loaded:
                # If still not found, try loading directly with fallback
                try:
                    validation = validate_raster_input(inp)
                    if not validation.valid:
                        if errors is not None:
                            errors.extend(validation.errors)
                        continue
                    if validation.valid:
                        resolved.append(load_raster(inp))
                except Exception:
                    pass
        return resolved
