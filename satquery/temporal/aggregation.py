from typing import List


class TemporalAggregation:
    """Aggregate measurements across a temporal sequence."""

    def __init__(self, measurements: List[float]):
        self.measurements = [float(value) for value in measurements]

    def summary(self):
        """Return basic and extended temporal statistics."""

        if not self.measurements:
            return {}

        first = self.measurements[0]
        last = self.measurements[-1]
        delta = last - first

        if first != 0:
            percentage_change = (delta / abs(first)) * 100
        else:
            percentage_change = None

        return {
            "first": first,
            "last": last,
            "delta": delta,
            "mean": sum(self.measurements) / len(self.measurements),
            "minimum": min(self.measurements),
            "maximum": max(self.measurements),
            "range": max(self.measurements) - min(self.measurements),
            "count": len(self.measurements),
            "percentage_change": percentage_change,
            "trend": calculate_trend(self.measurements),
        }


def calculate_trend(
    measurements: List[float],
    tolerance: float = 0.5
):
    """Classify the overall temporal trend."""

    if len(measurements) < 2:
        return "INSUFFICIENT_DATA"

    delta = measurements[-1] - measurements[0]

    if delta > tolerance:
        return "INCREASING"

    if delta < -tolerance:
        return "DECREASING"

    return "STABLE"
