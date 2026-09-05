import uuid

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ChangeEvent:
    event_id: str
    track_id: str
    start_time: str
    end_time: str
    state: str
    measurements: List[float] = field(default_factory=list)


def create_change_event(track) -> ChangeEvent:
    """Create a change event from a tracked region."""

    if not track.timestamps:
        start_time = "unknown"
        end_time = "unknown"
    else:
        start_time = track.timestamps[0]
        end_time = track.timestamps[-1]

    if len(track.measurements) >= 2:
        state = (
            "changed"
            if track.measurements[0] != track.measurements[-1]
            else "unchanged"
        )
    else:
        state = "unknown"

    return ChangeEvent(
        event_id=str(uuid.uuid4()),
        track_id=track.track_id,
        start_time=start_time,
        end_time=end_time,
        state=state,
        measurements=list(track.measurements)
    )