
import numpy as np

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence


class SemanticChangeTool(SatQueryTool):
    name = "semantic_change"
    description = "Analyzes semantic land-cover transitions between two temporal label maps."
    capabilities = ToolCapabilities(metadata=True)

    LABELS = {
        0: "background",
        1: "low_vegetation",
        2: "nvg_surface",
        3: "tree",
        4: "water",
        5: "Building",
        6: "Playground",
    }

    def execute(self, context, arguments: dict) -> ToolResult:
        label_t1 = arguments.get("label_t1")
        label_t2 = arguments.get("label_t2")

        if label_t1 is None or label_t2 is None:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Two semantic label maps required"],
            )

        label_t1 = np.asarray(label_t1)
        label_t2 = np.asarray(label_t2)

        if label_t1.shape != label_t2.shape:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["T1 and T2 label maps must have the same dimensions"],
            )

        transitions = {}
        valid_pixels = 0

        for class_t1 in np.unique(label_t1):
            for class_t2 in np.unique(label_t2):
                count = int(
                    np.count_nonzero(
                        (label_t1 == class_t1) &
                        (label_t2 == class_t2)
                    )
                )

                if count == 0:
                    continue

                valid_pixels += count

                if class_t1 != class_t2:
                    name_t1 = self.LABELS.get(
                        int(class_t1),
                        f"unknown_{class_t1}"
                    )
                    name_t2 = self.LABELS.get(
                        int(class_t2),
                        f"unknown_{class_t2}"
                    )

                    key = f"{name_t1}->{name_t2}"
                    transitions[key] = count

        total_changed_pixels = sum(transitions.values())

        data = {
            "transitions": transitions,
            "total_changed_pixels": total_changed_pixels,
            "valid_pixels": valid_pixels,
            "change_percentage": (
                total_changed_pixels / valid_pixels * 100
                if valid_pixels > 0
                else 0.0
            ),
        }

        ev = Evidence(
            source_type="semantic_raster_analysis",
            source="T1/T2 semantic label maps",
            tool=self.name,
            metadata=data,
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
            evidence=[ev],
        )
