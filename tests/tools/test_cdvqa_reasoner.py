
from satquery.tools.cdvqa_reasoner import CDVQAReasoner


def _reasoner():
    return CDVQAReasoner()


def _semantic_result():
    return {
        "transitions": {
            "NVG_surface->buildings": 1472,
            "buildings->NVG_surface": 3170,
        },
        "total_changed_pixels": 4642,
        "valid_pixels": 262144,
    }


def _class_counts():
    return {
        "t1": {
            "NVG_surface": 1472,
            "buildings": 3170,
        },
        "t2": {
            "NVG_surface": 3170,
            "buildings": 1472,
        },
    }


def test_cdvqa_change_or_not():
    reasoner = _reasoner()

    expected = {
        "Did the areas of non-vegetated ground surface change?": "yes",
        "Did the regions of trees change?": "no",
        "Have the areas of low vegetation changed?": "no",
        "Have the regions of water changed?": "no",
        "Have the regions of playgrounds changed?": "no",
        "Have the regions of buildings changed?": "yes",
    }

    for question, expected_answer in expected.items():
        result = reasoner.execute(
            context=None,
            arguments={
                "question": question,
                "question_type": "change_or_not",
                "semantic_result": _semantic_result(),
            },
        )

        assert result.success is True
        assert result.data["answer"] == expected_answer


def test_cdvqa_increase_decrease():
    reasoner = _reasoner()

    increase = reasoner.execute(
        context=None,
        arguments={
            "question": "Have the regions of buildings increased?",
            "question_type": "increase_or_not",
            "semantic_result": _semantic_result(),
            "class_counts": _class_counts(),
        },
    )

    decrease = reasoner.execute(
        context=None,
        arguments={
            "question": "Did the regions of buildings decrease?",
            "question_type": "decrease_or_not",
            "semantic_result": _semantic_result(),
            "class_counts": _class_counts(),
        },
    )

    assert increase.success is True
    assert increase.data["answer"] == "no"

    assert decrease.success is True
    assert decrease.data["answer"] == "yes"


def test_cdvqa_change_ratio():
    reasoner = _reasoner()

    result = reasoner.execute(
        context=None,
        arguments={
            "question": "What is the percentage of changed regions?",
            "question_type": "change_ratio",
            "semantic_result": _semantic_result(),
        },
    )

    assert result.success is True
    assert result.data["answer"] == "0_to_10"


def test_cdvqa_change_ratio_types():
    reasoner = _reasoner()

    result = reasoner.execute(
        context=None,
        arguments={
            "question": "What percentage of trees changed?",
            "question_type": "change_ratio_types",
            "semantic_result": _semantic_result(),
            "class_counts": _class_counts(),
            "image_side": "t1",
        },
    )

    assert result.success is True
    assert result.data["answer"] == "0"


def test_cdvqa_directional_ranking():
    reasoner = _reasoner()

    cases = [
        (
            "What is the smallest change in the first image?",
            "t1",
            "nvg_surface",
        ),
        (
            "What is the largest change in the pre-change image?",
            "t1",
            "buildings",
        ),
        (
            "What type of change is the smallest in the post-change image?",
            "t2",
            "buildings",
        ),
        (
            "What is the largest change in the second image?",
            "t2",
            "nvg_surface",
        ),
    ]

    for question, image_side, expected in cases:
        result = reasoner.execute(
            context=None,
            arguments={
                "question": question,
                "question_type": "auto",
                "semantic_result": _semantic_result(),
                "class_counts": _class_counts(),
                "image_side": image_side,
            },
        )

        assert result.success is True
        assert result.data["answer"] == expected


def test_cdvqa_automatic_image_side():
    reasoner = _reasoner()

    cases = [
        (
            "What is the smallest change in the first image?",
            "nvg_surface",
        ),
        (
            "What is the largest change in the pre-change image?",
            "buildings",
        ),
        (
            "What type of change is the smallest in the post-change image?",
            "buildings",
        ),
        (
            "What is the largest change in the second image?",
            "nvg_surface",
        ),
    ]

    for question, expected in cases:
        result = reasoner.execute(
            context=None,
            arguments={
                "question": question,
                "question_type": "auto",
                "semantic_result": _semantic_result(),
                "class_counts": _class_counts(),
            },
        )

        assert result.success is True
        assert result.data["answer"] == expected
