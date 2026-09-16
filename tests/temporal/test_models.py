import pytest
from dataclasses import dataclass
from datetime import datetime

from satquery.temporal.models import TemporalSeries


@dataclass
class MockImage:
    path: str
    acquisition_time: datetime = None


def make_image(path, acquisition_time):
    return MockImage(
        path=path,
        acquisition_time=acquisition_time,
    )


def test_temporal_series_requires_observations():
    with pytest.raises(ValueError, match="at least one observation"):
        TemporalSeries([])


def test_temporal_series_requires_acquisition_time():
    image = make_image("t1.tif", None)

    with pytest.raises(ValueError, match="missing acquisition_time"):
        TemporalSeries([image])


def test_temporal_series_sorts_chronologically():
    t1 = make_image("t1.tif", datetime(2025, 1, 1))
    t2 = make_image("t2.tif", datetime(2024, 1, 1))

    series = TemporalSeries([t1, t2])

    assert series.first().path == "t2.tif"
    assert series.last().path == "t1.tif"


def test_temporal_series_rejects_duplicate_timestamps():
    time = datetime(2025, 1, 1)

    t1 = make_image("t1.tif", time)
    t2 = make_image("t2.tif", time)

    with pytest.raises(ValueError, match="Duplicate timestamps"):
        TemporalSeries([t1, t2])


def test_temporal_series_pairwise():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))
    t3 = make_image("t3.tif", datetime(2026, 1, 1))

    series = TemporalSeries([t1, t2, t3])

    pairs = series.pairwise()

    assert len(pairs) == 2
    assert pairs[0] == (t1, t2)
    assert pairs[1] == (t2, t3)


def test_temporal_series_timestamps():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))

    series = TemporalSeries([t1, t2])

    assert series.timestamps() == [
        datetime(2024, 1, 1),
        datetime(2025, 1, 1),
    ]


def test_temporal_series_length():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))

    series = TemporalSeries([t1, t2])

    assert len(series) == 2


def test_temporal_series_is_chronological():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))

    series = TemporalSeries([t2, t1])

    assert series.is_chronological() is True


def test_temporal_series_get_pair():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))
    t3 = make_image("t3.tif", datetime(2026, 1, 1))

    series = TemporalSeries([t1, t2, t3])

    assert series.get_pair(0) == (t1, t2)
    assert series.get_pair(1) == (t2, t3)


def test_temporal_series_get_pair_invalid_index():
    t1 = make_image("t1.tif", datetime(2024, 1, 1))
    t2 = make_image("t2.tif", datetime(2025, 1, 1))

    series = TemporalSeries([t1, t2])

    with pytest.raises(IndexError):
        series.get_pair(1)
