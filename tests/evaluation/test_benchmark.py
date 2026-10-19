import math
import json
import shutil

import pytest

from satquery.evaluation.benchmark import BenchmarkEngine
from satquery.evaluation.metrics import bleu1, contains_match, exact_match, iou, token_f1


def test_text_metrics():
    assert exact_match("Yes.", "yes") == 1.0
    assert exact_match("There are two ships", "2") == 0.0
    assert contains_match("There are two ships", "2") == 1.0
    assert contains_match("There are 12 ships", "2") == 0.0
    assert token_f1("a large harbor", "harbor") == pytest.approx(2 * 0.5 * 1 / 1.5)
    assert bleu1("harbor", "harbor") == 1.0
    assert bleu1("harbor", "large busy harbor") == pytest.approx(math.exp(1 - 3))
    assert bleu1("", "harbor") == 0.0


def test_iou():
    assert iou((0, 0, 2, 2), (1, 1, 3, 3)) == pytest.approx(1 / 7)
    assert iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0.0


@pytest.fixture
def vrsbench_like(tmp_path):
    """VRSBench layout: annotations reference images by image_id in a sibling folder."""
    (tmp_path / "Images_val").mkdir()
    shutil.copy("test1.tif", tmp_path / "Images_val" / "00001.tif")
    annotations = [
        {"question_id": 1, "image_id": "00001.tif", "question": "Is there water?", "ground_truth": "yes", "type": "presence"},
        {"question_id": 2, "image_id": "00001.tif", "question": "How many ships?", "ground_truth": "", "type": "count"},
        {"question_id": 3, "image_id": "missing.tif", "question": "Is there a road?", "ground_truth": "no", "type": "presence"},
    ]
    (tmp_path / "VRSBench_EVAL_vqa.json").write_text(json.dumps(annotations))
    return tmp_path


def test_loader_resolves_image_id_and_skips_unlabeled(vrsbench_like):
    engine = BenchmarkEngine(str(vrsbench_like), max_samples=10)
    samples = engine.load_dataset()

    assert [s["id"] for s in samples] == [1]
    assert samples[0]["image"].endswith("00001.tif")
    assert dict(engine.skipped) == {"no_ground_truth": 1, "image_not_found": 1}


def test_run_scores_mock_provider_honestly(vrsbench_like):
    summary = BenchmarkEngine(str(vrsbench_like), max_samples=10).run(provider_name="mock")

    assert summary["samples_evaluated"] == 1
    assert summary["model"] == "satquery-mock"
    # The mock answer does not contain "yes", so it must not score.
    assert summary["metrics_percent"]["exact_match"] == 0.0
    assert summary["metrics_percent"]["contains_match"] == 0.0


def test_run_refuses_unlabeled_dataset(tmp_path):
    shutil.copy("test1.tif", tmp_path / "scene.tif")
    with pytest.raises(ValueError, match="No annotated samples"):
        BenchmarkEngine(str(tmp_path)).run(provider_name="mock")
