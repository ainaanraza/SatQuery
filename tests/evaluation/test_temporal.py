from satquery.evaluation.temporal import evaluate_temporal


def test_evaluate_temporal_counts_successful_and_failed_pairs():
    dataset = [
        {"image_a": "t1.tif", "image_b": "t2.tif", "success": True},
        {"image_a": "t2.tif", "image_b": "t3.tif", "success": False},
        {"image_a": "t3.tif", "image_b": "t4.tif", "success": True},
    ]

    result = evaluate_temporal(dataset)

    assert result["successful_pairs"] == 2
    assert result["failed_pairs"] == 1