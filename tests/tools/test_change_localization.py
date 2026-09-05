import numpy as np
from rasterio.transform import from_origin

from satquery.tools.change_localization import ChangeLocalizationTool


def test_change_localization_uses_change_mask():
    change_mask = np.array([
        [False, True],
        [False, True]
    ])

    tool = ChangeLocalizationTool()

    result = tool.execute(
        context=None,
        arguments={
            "mask": change_mask,
            "pixel_area_sqm": 100
        }
    )

    assert result.success is True
    assert result.data["changed_pixel_count"] == 2
    assert result.data["changed_area_sqm"] == 200

def test_change_localization_calculates_bounds():
    change_mask = np.array([
        [False, True, False],
        [False, True, False],
        [False, False, False]
    ])

    tool = ChangeLocalizationTool()

    result = tool.execute(
        context=None,
        arguments={
            "mask": change_mask,
            "pixel_area_sqm": 100,
            "transform": from_origin(0, 3, 1, 1)
        }
    )

    assert result.success is True
    assert result.data["overall_change_bounds"] == (1.0, 1.0, 2.0, 3.0)