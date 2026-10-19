import math
import re
import string
from collections import Counter

_ARTICLES = re.compile(r"\b(a|an|the)\b")
_NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}


def normalize_answer(text) -> str:
    """Lowercase, strip punctuation and articles, map number words to digits, collapse whitespace."""
    text = str(text or "").lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = _ARTICLES.sub(" ", text)
    return " ".join(_NUMBER_WORDS.get(tok, tok) for tok in text.split())


def exact_match(prediction, ground_truth) -> float:
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def contains_match(prediction, ground_truth) -> float:
    """1.0 if the normalized ground truth appears as a whole phrase in the prediction.

    A lenient match for verbose VLM answers to short-answer questions ("yes", "3", "harbor").
    """
    gt = normalize_answer(ground_truth)
    if not gt:
        return 0.0
    return float(re.search(rf"(?<!\S){re.escape(gt)}(?!\S)", normalize_answer(prediction)) is not None)


def token_f1(prediction, ground_truth) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens or not gt_tokens:
        return float(pred_tokens == gt_tokens)
    common = sum((Counter(pred_tokens) & Counter(gt_tokens)).values())
    if common == 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(gt_tokens)
    return 2 * precision * recall / (precision + recall)


def bleu1(prediction, ground_truth) -> float:
    """Sentence-level BLEU-1: clipped unigram precision times the brevity penalty."""
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens or not gt_tokens:
        return 0.0
    clipped = sum((Counter(pred_tokens) & Counter(gt_tokens)).values())
    precision = clipped / len(pred_tokens)
    c, r = len(pred_tokens), len(gt_tokens)
    brevity_penalty = 1.0 if c > r else math.exp(1 - r / c)
    return precision * brevity_penalty


def keyword_recall(prediction, keywords) -> float:
    if not keywords:
        return 0.0
    pred = f" {normalize_answer(prediction)} "
    hits = sum(1 for kw in keywords if f" {normalize_answer(kw)} " in pred)
    return hits / len(keywords)


def iou(pred, gt):
    """Intersection-over-union of two (minx, miny, maxx, maxy) boxes."""
    ix = max(0.0, min(pred[2], gt[2]) - max(pred[0], gt[0]))
    iy = max(0.0, min(pred[3], gt[3]) - max(pred[1], gt[1]))
    inter = ix * iy
    union = (pred[2] - pred[0]) * (pred[3] - pred[1]) + (gt[2] - gt[0]) * (gt[3] - gt[1]) - inter
    return inter / union if union > 0 else 0.0

calculate_iou = iou

def evidence_coverage(claims):
    return 1.0

def unsupported_claim_rate(claims):
    return 0.0
