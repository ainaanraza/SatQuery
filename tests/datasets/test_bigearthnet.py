from pathlib import Path

import pytest

from satquery.datasets.bigearthnet import BigEarthNetDataset


MANIFEST = Path("data/bigearthnet/bench_pairs.csv")


def test_bigearthnet_manifest_exists():
    assert MANIFEST.exists()


def test_bigearthnet_loads_benchmark_pairs():
    dataset = BigEarthNetDataset(MANIFEST)

    assert len(dataset) == 1082


def test_bigearthnet_pair_contains_required_metadata():
    dataset = BigEarthNetDataset(MANIFEST)

    pair = dataset.get_pair(0)

    assert pair["s1_name"].startswith("S1")
    assert pair["patch_id"].startswith("S2")
    assert pair["country"] == "Austria"
    assert pair["season"] == "Summer"


def test_bigearthnet_invalid_index():
    dataset = BigEarthNetDataset(MANIFEST)

    with pytest.raises(IndexError):
        dataset.get_pair(1082)


def test_bigearthnet_loads_annotations():
    dataset = BigEarthNetDataset(
        MANIFEST,
        "data/bigearthnet/bench_annotations.csv",
    )

    annotations = dataset.load_annotations()

    assert len(annotations) == 15029


def test_bigearthnet_get_annotations_for_pair():
    dataset = BigEarthNetDataset(
        MANIFEST,
        "data/bigearthnet/bench_annotations.csv",
    )

    pair = dataset.get_pair(0)
    annotations = dataset.get_annotations(pair["patch_id"])

    assert len(annotations) > 0
    assert all(
        annotation["patch_id"] == pair["patch_id"]
        for annotation in annotations
    )
