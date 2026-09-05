from satquery.temporal.aggregation import (
    TemporalAggregation,
    calculate_trend
)


def test_temporal_summary():
    aggregation = TemporalAggregation([10.0, 15.0, 20.0])

    result = aggregation.summary()

    assert result["first"] == 10.0
    assert result["last"] == 20.0
    assert result["delta"] == 10.0
    assert result["mean"] == 15.0


def test_increasing_trend():
    assert calculate_trend([10.0, 15.0, 20.0]) == "INCREASING"


def test_decreasing_trend():
    assert calculate_trend([20.0, 15.0, 10.0]) == "DECREASING"


def test_stable_trend():
    assert calculate_trend([10.0, 10.2, 10.1]) == "STABLE"


def test_insufficient_data():
    assert calculate_trend([10.0]) == "INSUFFICIENT_DATA"