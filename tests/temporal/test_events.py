from satquery.temporal.events import ChangeEvent


def test_change_event_can_be_created():
    event = ChangeEvent(
        event_id="event-1",
        track_id="track-1",
        start_time="2024-01-01",
        end_time="2025-01-01",
        state="changed",
        measurements=[10.0, 20.0]
    )

    assert event.event_id == "event-1"
    assert event.track_id == "track-1"
    assert event.state == "changed"
    assert event.measurements == [10.0, 20.0]


def test_change_event_from_track():
    from satquery.temporal.events import create_change_event
    from satquery.temporal.tracking import RegionTrack

    track = RegionTrack(
        track_id="track-1",
        geometries=[
            {
                "min_row": 1,
                "min_col": 1,
                "max_row": 2,
                "max_col": 2,
                "pixel_count": 4
            },
            {
                "min_row": 1,
                "min_col": 1,
                "max_row": 2,
                "max_col": 2,
                "pixel_count": 6
            }
        ],
        timestamps=["2024-01-01", "2025-01-01"],
        measurements=[4.0, 6.0]
    )

    event = create_change_event(track)

    assert isinstance(event, ChangeEvent)
    assert event.track_id == "track-1"
    assert event.start_time == "2024-01-01"
    assert event.end_time == "2025-01-01"
    assert event.state == "changed"
    assert event.measurements == [4.0, 6.0]