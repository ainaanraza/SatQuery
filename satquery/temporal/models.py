from typing import List
from satquery.inputs.models import RSImage


class TemporalSeries:
    def __init__(self, observations: List[RSImage]):
        if not observations:
            raise ValueError("TemporalSeries requires at least one observation.")

        for obs in observations:
            if not obs.acquisition_time:
                raise ValueError(
                    f"Observation {obs.path} missing acquisition_time."
                )

        # Sort chronologically by acquisition_time.
        self.observations = sorted(
            observations,
            key=lambda x: x.acquisition_time
        )

        # Check for duplicate timestamps.
        times = [obs.acquisition_time for obs in self.observations]

        if len(times) != len(set(times)):
            raise ValueError("Duplicate timestamps found in TemporalSeries.")

    def __len__(self):
        """Return the number of temporal observations."""
        return len(self.observations)

    def is_chronological(self):
        """Return True when observations are in chronological order."""
        return all(
            self.observations[i].acquisition_time
            < self.observations[i + 1].acquisition_time
            for i in range(len(self.observations) - 1)
        )

    def pairwise(self):
        """Return consecutive observations as chronological pairs."""
        return [
            (self.observations[i], self.observations[i + 1])
            for i in range(len(self.observations) - 1)
        ]

    def get_pair(self, index):
        """
        Return one consecutive temporal pair.

        For N observations, valid pair indices are 0 through N-2.
        """
        if index < 0 or index >= len(self.observations) - 1:
            raise IndexError(
                f"Temporal pair index {index} out of range."
            )

        return (
            self.observations[index],
            self.observations[index + 1],
        )

    def first(self):
        """Return the earliest observation."""
        return self.observations[0]

    def last(self):
        """Return the latest observation."""
        return self.observations[-1]

    def timestamps(self):
        """Return observation timestamps in chronological order."""
        return [
            obs.acquisition_time
            for obs in self.observations
        ]
