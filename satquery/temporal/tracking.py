import uuid

from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np


@dataclass
class RegionTrack:
    track_id: str
    geometries: List[Dict] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    measurements: List[float] = field(default_factory=list)


def _find_regions(mask):
    """Find connected True regions using 4-neighbour connectivity."""

    mask = np.asarray(mask, dtype=bool)

    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)

    regions = []

    for row in range(height):
        for col in range(width):

            if not mask[row, col] or visited[row, col]:
                continue

            stack = [(row, col)]
            visited[row, col] = True

            pixels = []

            while stack:
                current_row, current_col = stack.pop()
                pixels.append((current_row, current_col))

                neighbours = [
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ]

                for next_row, next_col in neighbours:

                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and mask[next_row, next_col]
                        and not visited[next_row, next_col]
                    ):
                        visited[next_row, next_col] = True
                        stack.append((next_row, next_col))

            rows = [pixel[0] for pixel in pixels]
            cols = [pixel[1] for pixel in pixels]

            regions.append({
                "min_row": min(rows),
                "min_col": min(cols),
                "max_row": max(rows),
                "max_col": max(cols),
                "pixel_count": len(pixels)
            })

    return regions


def _region_iou(region_a, region_b):
    """Calculate IoU between two rectangular region bounds."""

    min_row = max(region_a["min_row"], region_b["min_row"])
    min_col = max(region_a["min_col"], region_b["min_col"])

    max_row = min(region_a["max_row"], region_b["max_row"])
    max_col = min(region_a["max_col"], region_b["max_col"])

    if min_row > max_row or min_col > max_col:
        return 0.0

    intersection = (
        (max_row - min_row + 1)
        * (max_col - min_col + 1)
    )

    area_a = (
        (region_a["max_row"] - region_a["min_row"] + 1)
        * (region_a["max_col"] - region_a["min_col"] + 1)
    )

    area_b = (
        (region_b["max_row"] - region_b["min_row"] + 1)
        * (region_b["max_col"] - region_b["min_col"] + 1)
    )

    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


def track_regions(t1_mask, t2_mask, threshold_iou=0.5):
    """Track regions between two temporal masks using IoU."""

    t1_regions = _find_regions(t1_mask)
    t2_regions = _find_regions(t2_mask)

    tracks = []
    matched_t2 = set()

    for region_a in t1_regions:

        best_match = None
        best_iou = 0.0

        for index, region_b in enumerate(t2_regions):

            if index in matched_t2:
                continue

            iou = _region_iou(region_a, region_b)

            if iou > best_iou:
                best_iou = iou
                best_match = index

        track = RegionTrack(
            track_id=str(uuid.uuid4()),
            geometries=[region_a],
            measurements=[float(region_a["pixel_count"])]
        )

        if best_match is not None and best_iou >= threshold_iou:

            track.geometries.append(t2_regions[best_match])

            track.measurements.append(
                float(t2_regions[best_match]["pixel_count"])
            )

            matched_t2.add(best_match)

        tracks.append(track)

    # Regions appearing only in T2 become new tracks.
    for index, region_b in enumerate(t2_regions):

        if index not in matched_t2:

            tracks.append(
                RegionTrack(
                    track_id=str(uuid.uuid4()),
                    geometries=[region_b],
                    measurements=[float(region_b["pixel_count"])]
                )
            )

    return tracks