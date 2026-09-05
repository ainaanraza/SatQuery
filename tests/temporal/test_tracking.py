import numpy as np

from satquery.temporal.tracking import track_regions


def test_identical_regions_are_tracked_together():
    t1_mask = np.array([
        [False, True],
        [False, True]
    ])

    t2_mask = np.array([
        [False, True],
        [False, True]
    ])

    tracks = track_regions(t1_mask, t2_mask)

    assert len(tracks) == 1
    assert len(tracks[0].geometries) == 2


def test_changed_regions_are_not_empty():
    t1_mask = np.array([
        [False, True],
        [False, True]
    ])

    t2_mask = np.array([
        [False, False],
        [False, True]
    ])

    tracks = track_regions(t1_mask, t2_mask)

    assert len(tracks) >= 1
    assert any(len(track.geometries) > 0 for track in tracks)