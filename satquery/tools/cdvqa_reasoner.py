
import re

from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence


class CDVQAReasoner(SatQueryTool):
    name = "cdvqa_reasoner"
    description = "Answers semantic change questions using temporal transition evidence."
    capabilities = ToolCapabilities(metadata=True)

    CLASS_ALIASES = {
        "nvg_surface": [
            "nvg surface",
            "non-vegetated ground surface",
            "non vegetated ground surface",
            "nvg",
        ],
        "low_vegetation": [
            "low vegetation",
        ],
        "trees": [
            "trees",
            "tree",
        ],
        "water": [
            "water",
        ],
        "buildings": [
            "buildings",
            "building",
        ],
        "playgrounds": [
            "playgrounds",
            "playground",
        ],
    }

    def _normalize_class(self, name):
        name = name.strip().lower()

        aliases = {
            "building": "buildings",
            "buildings": "buildings",
            "tree": "trees",
            "trees": "trees",
            "playground": "playgrounds",
            "playgrounds": "playgrounds",
        }

        return aliases.get(name, name)

    def _find_class(self, question):
        q = question.lower()

        for class_name, aliases in self.CLASS_ALIASES.items():
            for alias in aliases:
                if re.search(r"(?<![a-z0-9_])" + re.escape(alias) + r"(?![a-z0-9_])", q):
                    return class_name

        return None

    def _class_changed(self, transitions, class_name):
        class_name = class_name.strip().lower()

        for transition, count in transitions.items():
            if count <= 0:
                continue

            source, target = transition.split("->", 1)
            source = source.strip().lower()
            target = target.strip().lower()

            if source == class_name or target == class_name:
                return True

        return False

    def _class_area_change(self, class_counts, class_name):
        class_name = class_name.strip().lower()

        t1_counts = {
            self._normalize_class(str(k)): v
            for k, v in class_counts.get("t1", {}).items()
        }

        t2_counts = {
            self._normalize_class(str(k)): v
            for k, v in class_counts.get("t2", {}).items()
        }

        t1 = t1_counts.get(class_name, 0)
        t2 = t2_counts.get(class_name, 0)

        return t1, t2

    def _ratio_bucket(self, percentage):
        if percentage <= 0:
            return "0"

        lower = int(percentage // 10) * 10
        upper = lower + 10

        if lower >= 90:
            return "90_to_100"

        return f"{lower}_to_{upper}"

    def _rank_change(self, transitions, direction, image_side):
        changes = {}

        for transition, count in transitions.items():
            if count <= 0:
                continue

            source, target = transition.split("->", 1)
            source = source.strip().lower()
            target = target.strip().lower()

            class_name = source if image_side == "t1" else target

            changes[class_name] = changes.get(class_name, 0) + count

        if not changes:
            return None

        if direction == "smallest":
            return min(changes, key=changes.get)

        return max(changes, key=changes.get)

    def execute(self, context, arguments: dict) -> ToolResult:
        question = arguments.get("question")
        semantic_result = arguments.get("semantic_result")

        if not question:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Question required"],
            )

        if not semantic_result:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Semantic change result required"],
            )

        transitions = semantic_result.get("transitions", {})

        question_type = arguments.get("question_type", "auto")

        if question_type == "auto":
            q = question.lower().strip()

            if "what is the percentage of changed" in q:
                question_type = "change_ratio"
            elif "what percentage of" in q:
                question_type = "change_ratio_types"
            elif "change ratio" in q:
                question_type = "change_ratio"
            elif "what have" in q and "changed to" in q:
                question_type = "change_to_what"
            elif "changed to" in q:
                question_type = "change_to_what"
            elif "smallest change" in q or ("smallest" in q and "change" in q):
                question_type = "smallest_change"
            elif "largest change" in q or ("largest" in q and "change" in q):
                question_type = "largest_change"
            elif "increase" in q or "increased" in q:
                question_type = "increase_or_not"
            elif "decrease" in q or "decreased" in q:
                question_type = "decrease_or_not"
            else:
                question_type = "change_or_not"

        class_name = self._find_class(question)

        if question_type in {
            "change_or_not",
            "increase_or_not",
            "decrease_or_not",
            "change_to_what",
            "change_ratio_types",
        } and class_name is None:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["Could not identify land-cover class in question"],
            )

        if "image_side" not in arguments:
            q_lower = question.lower()

            if any(
                term in q_lower
                for term in [
                    "second image",
                    "post-change image",
                    "post change image",
                    "second",
                ]
            ):
                arguments["image_side"] = "t2"
            else:
                arguments["image_side"] = "t1"

        image_side = arguments.get("image_side", "t1").lower()

        if question_type == "change_or_not":
            changed = self._class_changed(transitions, class_name)
            answer = "yes" if changed else "no"

        elif question_type == "increase_or_not":
            class_counts = arguments.get("class_counts", {})
            t1, t2 = self._class_area_change(
                class_counts, class_name
            )
            answer = "yes" if t2 > t1 else "no"

        elif question_type == "decrease_or_not":
            class_counts = arguments.get("class_counts", {})
            t1, t2 = self._class_area_change(
                class_counts, class_name
            )
            answer = "yes" if t2 < t1 else "no"

        elif question_type == "change_to_what":
            candidates = {}

            for transition, count in transitions.items():
                if count <= 0:
                    continue

                source, target = transition.split("->", 1)
                source = self._normalize_class(source)
                target = self._normalize_class(target)

                if source == self._normalize_class(class_name):
                    candidates[target] = (
                        candidates.get(target, 0) + count
                    )

            if not candidates:
                answer = "no_change"
            else:
                answer = max(candidates, key=candidates.get)

        elif question_type in {"smallest_change", "largest_change"}:
            direction = (
                "smallest"
                if question_type == "smallest_change"
                else "largest"
            )

            answer = self._rank_change(
                transitions,
                direction,
                image_side,
            )

            if answer is None:
                answer = "no_change"

        elif question_type == "change_ratio":
            changed = semantic_result.get(
                "total_changed_pixels", 0
            )
            valid = semantic_result.get(
                "valid_pixels", 0
            )

            percentage = (
                changed / valid * 100
                if valid > 0
                else 0.0
            )

            answer = self._ratio_bucket(percentage)

        elif question_type == "change_ratio_types":
            class_counts = arguments.get("class_counts", {})

            t1_counts = {
                self._normalize_class(str(k)): v
                for k, v in class_counts.get("t1", {}).items()
            }

            t2_counts = {
                self._normalize_class(str(k)): v
                for k, v in class_counts.get("t2", {}).items()
            }

            target_counts = (
                t1_counts
                if image_side == "t1"
                else t2_counts
            )

            total_class_pixels = target_counts.get(
                self._normalize_class(class_name),
                0,
            )

            if total_class_pixels <= 0:
                percentage = 0.0
            else:
                changed_pixels = 0

                for transition, count in transitions.items():
                    if count <= 0:
                        continue

                    source, target = transition.split(
                        "->", 1
                    )

                    source = self._normalize_class(source)
                    target = self._normalize_class(target)
                    cls = self._normalize_class(class_name)

                    if (
                        image_side == "t1"
                        and source == cls
                    ) or (
                        image_side == "t2"
                        and target == cls
                    ):
                        changed_pixels += count

                percentage = (
                    changed_pixels
                    / total_class_pixels
                    * 100
                )

            answer = self._ratio_bucket(percentage)

        else:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=[
                    f"Unsupported CDVQA question type: {question_type}"
                ],
            )

        data = {
            "question": question,
            "question_type": question_type,
            "class": class_name,
            "image_side": image_side,
            "answer": answer,
        }

        ev = Evidence(
            source_type="cdvqa_reasoning",
            source="semantic change transitions",
            tool=self.name,
            metadata=data,
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
            evidence=[ev],
        )
