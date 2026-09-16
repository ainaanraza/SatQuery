
import numpy as np

from satquery.tools.temporal_validation import TemporalValidationTool


def test_temporal_validation_tracks_and_aggregates_change():
    tool = TemporalValidationTool()

    t1_mask = np.array([
        [False, True, True, False],
        [False, True, True, False],
        [False, False, False, False],
        [False, False, False, False],
    ])

    t2_mask = np.array([
        [False, True, True, False],
        [False, True, True, False],
        [False, False, True, False],
        [False, False, False, False],
    ])

    result = tool.execute(
        context=None,
        arguments={
            "t1_mask": t1_mask,
            "t2_mask": t2_mask,
            "t1_timestamp": "2024-01-01",
            "t2_timestamp": "2025-01-01",
        },
    )

    assert result.success is True
    assert result.errors == []

    assert result.data["track_count"] == 1
    assert result.data["event_count"] == 1
    assert result.data["state_counts"]["changed"] == 1

    event = result.data["events"][0]

    assert event["start_time"] == "2024-01-01"
    assert event["end_time"] == "2025-01-01"
    assert event["state"] == "changed"
    assert event["measurements"] == [4.0, 5.0]

    summary = result.data["aggregation"]

    assert summary["delta"] == 1.0
    assert summary["percentage_change"] == 25.0
    assert summary["trend"] == "INCREASING"
