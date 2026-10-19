import os
from typing import List
from satquery.inputs.models import RSImage
from satquery.inputs.raster_loader import load_raster
from satquery.inputs.exceptions import SatQueryInputError

class InputResolver:
    def resolve(self, inputs: List[str]) -> List[RSImage]:
        """Load each path as an RSImage; raises SatQueryInputError if any input cannot be loaded."""
        resolved = []
        for inp in inputs:
            candidate_paths = [
                inp,
                os.path.join(os.getcwd(), inp),
                os.path.join("/content/GeoChat", inp),
                os.path.join("/content/data/VRSBench", inp)
            ]
            existing = [p for p in candidate_paths if os.path.exists(p)]
            if not existing:
                raise SatQueryInputError(f"Input raster not found: {inp}")

            last_error = None
            for p in existing:
                try:
                    resolved.append(load_raster(p))
                    break
                except Exception as e:
                    last_error = e
            else:
                raise SatQueryInputError(f"Could not read input raster {inp}: {last_error}")
        return resolved
