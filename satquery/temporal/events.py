from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ChangeEvent:
    event_id: str
    track_id: str
    start_time: str
    end_time: str
    state: str
    measurements: List[float] = field(default_factory=list)
