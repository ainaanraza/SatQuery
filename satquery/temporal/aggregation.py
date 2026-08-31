from typing import List

class TemporalAggregation:
    def __init__(self, measurements: List[float]):
        self.measurements = measurements
        
    def summary(self):
        if not self.measurements:
            return {}
        return {
            "first": self.measurements[0],
            "last": self.measurements[-1],
            "delta": self.measurements[-1] - self.measurements[0],
            "mean": sum(self.measurements) / len(self.measurements)
        }

def calculate_trend(measurements: List[float], tolerance: float = 0.5):
    if len(measurements) < 2:
        return "INSUFFICIENT_DATA"
    
    delta = measurements[-1] - measurements[0]
    if delta > tolerance:
        return "INCREASING"
    elif delta < -tolerance:
        return "DECREASING"
    else:
        return "STABLE"
