from dataclasses import dataclass
from typing import List
from satquery.inputs.models import RSImage

class TemporalSeries:
    def __init__(self, observations: List[RSImage]):
        if not observations:
            raise ValueError("TemporalSeries requires at least one observation.")
        
        for obs in observations:
            if not obs.acquisition_time:
                raise ValueError(f"Observation {obs.path} missing acquisition_time.")
                
        # Sort chronologically by acquisition_time
        self.observations = sorted(observations, key=lambda x: x.acquisition_time)
        
        # Check for duplicates (simple validation)
        times = [obs.acquisition_time for obs in self.observations]
        if len(times) != len(set(times)):
            raise ValueError("Duplicate timestamps found in TemporalSeries.")

    def pairwise(self):
        pairs = []
        for i in range(len(self.observations) - 1):
            pairs.append((self.observations[i], self.observations[i+1]))
        return pairs

    def first(self):
        return self.observations[0]

    def last(self):
        return self.observations[-1]

    def timestamps(self):
        return [obs.acquisition_time for obs in self.observations]
