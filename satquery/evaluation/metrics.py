import numpy as np


def iou(pred, gt):
    pred = np.asarray(pred, dtype=bool)
    gt = np.asarray(gt, dtype=bool)

    if pred.shape != gt.shape:
        raise ValueError("Prediction and ground truth must have the same shape")

    intersection = np.logical_and(pred, gt).sum()
    union = np.logical_or(pred, gt).sum()

    if union == 0:
        return 1.0

    return float(intersection / union)


calculate_iou = iou


def evidence_coverage(claims):
    if not claims:
        return 0.0

    supported_claims = sum(
        1 for claim in claims
        if claim.get("supported") is True
    )

    return supported_claims / len(claims)


def unsupported_claim_rate(claims):
    if not claims:
        return 0.0

    unsupported_claims = sum(
        1 for claim in claims
        if claim.get("supported") is False
    )

    return unsupported_claims / len(claims)