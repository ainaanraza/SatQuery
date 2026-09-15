
import numpy as np
import rasterio
from pathlib import Path

from satquery.tools.change_detection import ChangeDetectionTool


ROOT = Path("/content/SECOND/SECOND/test")
T1_DIR = ROOT / "T1"
T2_DIR = ROOT / "T2"
GT_DIR = ROOT / "GT_CD"


class Img:
    def __init__(self, path):
        self.path = str(path)


def main(limit=20):
    tool = ChangeDetectionTool()

    tp = fp = fn = 0
    evaluated = 0

    for t1_path in sorted(T1_DIR.glob("*.png"))[:limit]:
        name = t1_path.name
        t2_path = T2_DIR / name
        gt_path = GT_DIR / name

        if not t2_path.exists() or not gt_path.exists():
            continue

        result = tool.execute(
            context=None,
            arguments={
                "image_a": Img(t1_path),
                "image_b": Img(t2_path),
                "method": "absolute_difference",
            },
        )

        if not result.success:
            continue

        pred = result.data["mask"]

        with rasterio.open(gt_path) as gt:
            actual = gt.read(1) > 0

        tp += int(np.count_nonzero(pred & actual))
        fp += int(np.count_nonzero(pred & ~actual))
        fn += int(np.count_nonzero(~pred & actual))

        evaluated += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0

    print(f"Pairs evaluated: {evaluated}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"IoU: {iou:.4f}")
    print(f"TP: {tp}")
    print(f"FP: {fp}")
    print(f"FN: {fn}")


if __name__ == "__main__":
    main()
