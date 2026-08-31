import pytest
from satquery.temporal.models import TemporalSeries
from satquery.temporal.aggregation import calculate_trend
from satquery.inputs.models import RSImage

def mock_rsimage(path, acq_time=None, crs="EPSG:4326"):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=acq_time,
        crs=crs,
        bounds=(0,0,10,10),
        transform=None,
        width=100,
        height=100,
        resolution_x=1,
        resolution_y=1,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )

def test_temporal_ordering():
    t3 = mock_rsimage("t3.tif", "2024-03-01")
    t1 = mock_rsimage("t1.tif", "2024-01-01")
    t4 = mock_rsimage("t4.tif", "2024-04-01")
    t2 = mock_rsimage("t2.tif", "2024-02-01")
    
    series = TemporalSeries([t3, t1, t4, t2])
    assert series.first().path == "t1.tif"
    assert series.last().path == "t4.tif"
    
    pairs = series.pairwise()
    assert len(pairs) == 3
    assert pairs[0][0].path == "t1.tif" and pairs[0][1].path == "t2.tif"
    assert pairs[1][0].path == "t2.tif" and pairs[1][1].path == "t3.tif"

def test_missing_timestamp():
    t1 = mock_rsimage("t1.tif")
    with pytest.raises(ValueError):
        TemporalSeries([t1])

def test_duplicate_timestamp():
    t1 = mock_rsimage("t1.tif", "2024-01-01")
    t2 = mock_rsimage("t2.tif", "2024-01-01")
    with pytest.raises(ValueError):
        TemporalSeries([t1, t2])

def test_trend():
    assert calculate_trend([3, 7, 11]) == "INCREASING"
    assert calculate_trend([12, 8, 4]) == "DECREASING"
    assert calculate_trend([5, 5.01, 4.99], tolerance=0.1) == "STABLE"
    assert calculate_trend([5]) == "INSUFFICIENT_DATA"
