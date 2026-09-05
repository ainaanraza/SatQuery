import numpy as np

from satquery.evaluation.metrics import iou
from satquery.evaluation.metrics import evidence_coverage
from satquery.evaluation.metrics import unsupported_claim_rate


def test_iou_identical_masks():
    pred = np.array([
        [True, False],
        [False, True]
    ])

    gt = np.array([
        [True, False],
        [False, True]
    ])

    assert iou(pred, gt) == 1.0


def test_iou_no_overlap():
    pred = np.array([
        [True, False],
        [False, False]
    ])

    gt = np.array([
        [False, True],
        [False, False]
    ])

    assert iou(pred, gt) == 0.0


def test_iou_partial_overlap():
    pred = np.array([
        [True, True],
        [False, False]
    ])

    gt = np.array([
        [True, False],
        [True, False]
    ])

    # Intersection = 1, union = 3
    assert iou(pred, gt) == 1 / 3

def test_evidence_coverage():
    claims = [
        {"claim": "building detected", "supported": True},
        {"claim": "road detected", "supported": True},
        {"claim": "water detected", "supported": False},
    ]

    result = evidence_coverage(claims)

    assert result == 2 / 3    




def test_unsupported_claim_rate():
    claims = [
        {"claim": "building detected", "supported": True},
        {"claim": "road detected", "supported": False},
        {"claim": "water detected", "supported": False},
        {"claim": "forest detected", "supported": True},
    ]

    result = unsupported_claim_rate(claims)

    assert result == 0.5    