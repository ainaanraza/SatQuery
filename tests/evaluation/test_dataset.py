import json

from satquery.evaluation.dataset import DatasetManifest


def test_dataset_manifest_loads_json(tmp_path):
    manifest_path = tmp_path / "manifest.json"

    manifest_data = [
        {
            "image_a": "t1.tif",
            "image_b": "t2.tif",
            "split": "train"
        },
        {
            "image_a": "t3.tif",
            "image_b": "t4.tif",
            "split": "test"
        }
    ]

    manifest_path.write_text(
        json.dumps(manifest_data),
        encoding="utf-8"
    )

    manifest = DatasetManifest(manifest_path)

    result = manifest.load()

    assert result == manifest_data


def test_dataset_manifest_detects_split_leakage():
    manifest = DatasetManifest("dummy.json")

    splits = {
        "train": [
            {"image_a": "image1.tif", "image_b": "image2.tif"}
        ],
        "test": [
            {"image_a": "image2.tif", "image_b": "image3.tif"}
        ]
    }

    result = manifest.check_leakage(splits)

    assert result["leakage_detected"] is True
