import uuid

from dataclasses import dataclass, field
from typing import List


@dataclass
class ChangeEvent:
    event_id: str
    track_id: str
    start_time: str
    end_time: str
    state: str
    measurements: List[float] = field(default_factory=list)


def create_change_event(track) -> ChangeEvent:
    """
    Create a temporal change event from a RegionTrack.

    States:
    - changed: region exists in T1 and T2 and measurement changed
    - unchanged: region exists in T1 and T2 and measurement stayed the same
    - new: region appears only in T2
    - disappeared: region exists only in T1
    - unknown: insufficient temporal information
    """

    timestamps = list(track.timestamps)
    measurements = list(track.measurements)
    observation_sides = list(
        getattr(track, "observation_sides", [])
    )

    if timestamps:
        start_time = timestamps[0]
        end_time = timestamps[-1]
    else:
        start_time = "unknown"
        end_time = "unknown"

    # Use explicit observation provenance when available.
    if observation_sides == ["T1"]:
        state = "disappeared"

    elif observation_sides == ["T2"]:
        state = "new"

    elif observation_sides == ["T1", "T2"]:
        if len(measurements) >= 2:
            state = (
                "changed"
                if measurements[0] != measurements[-1]
                else "unchanged"
            )
        else:
            state = "unknown"

    # Backward compatibility:
    # Older RegionTrack objects may not contain observation_sides.
    elif len(measurements) >= 2:
        state = (
            "changed"
            if measurements[0] != measurements[-1]
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
        measurements=measurements,
    )
