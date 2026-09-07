import csv
from pathlib import Path


class BigEarthNetDataset:
    """Loader for the BigEarthNet.txt benchmark metadata."""

    PAIR_COLUMNS = {
        "s1_name",
        "patch_id",
        "latitude",
        "longitude",
        "country",
        "season",
        "climate_zone",
    }

    ANNOTATION_COLUMNS = {
        "ID",
        "s1_name",
        "patch_id",
        "input",
        "output",
        "type",
        "category",
        "latitude",
        "longitude",
        "country",
        "season",
        "climate_zone",
    }

    def __init__(self, pair_manifest_path, annotation_manifest_path=None):
        self.pair_manifest_path = Path(pair_manifest_path)
        self.annotation_manifest_path = (
            Path(annotation_manifest_path)
            if annotation_manifest_path
            else None
        )

    def _read_csv(self, path):
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        with path.open(
            "r",
            encoding="utf-8",
            newline=""
        ) as file:
            return list(csv.DictReader(file))

    def load_pairs(self):
        rows = self._read_csv(self.pair_manifest_path)

        if rows:
            missing = self.PAIR_COLUMNS - set(rows[0].keys())
            if missing:
                raise ValueError(
                    f"Missing pair columns: {sorted(missing)}"
                )

        return rows

    def load_annotations(self):
        if self.annotation_manifest_path is None:
            raise ValueError("Annotation manifest was not provided")

        rows = self._read_csv(self.annotation_manifest_path)

        if rows:
            missing = self.ANNOTATION_COLUMNS - set(rows[0].keys())
            if missing:
                raise ValueError(
                    f"Missing annotation columns: {sorted(missing)}"
                )

        return rows

    def __len__(self):
        return len(self.load_pairs())

    def get_pair(self, index):
        pairs = self.load_pairs()

        if index < 0 or index >= len(pairs):
            raise IndexError("BigEarthNet pair index out of range")

        return pairs[index]

    def get_annotations(self, patch_id=None):
        annotations = self.load_annotations()

        if patch_id is None:
            return annotations

        return [
            row
            for row in annotations
            if row["patch_id"] == patch_id
        ]