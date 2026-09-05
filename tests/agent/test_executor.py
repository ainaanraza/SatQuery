from datetime import datetime

import numpy as np
import rasterio
from rasterio.transform import from_origin
from satquery.tools.change_detection import ChangeDetectionTool
from satquery.tools.change_localization import ChangeLocalizationTool

from satquery.agent.executor import Executor
from satquery.agent.state import AgentState, ToolCall
from satquery.inputs.models import RSImage
from satquery.tools.registry import ToolRegistry


def create_test_raster(path, data):
    transform = from_origin(0, 2, 1, 1)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        nodata=0,
        transform=transform,
    ) as dst:
        dst.write(data, 1)


def mock_rsimage(path):
    return RSImage(
        path=str(path),
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=datetime(2024, 1, 1),
        crs="EPSG:4326",
        bounds=(0, 0, 2, 2),
        transform=from_origin(0, 2, 1, 1),
        width=2,
        height=2,
        resolution_x=1,
        resolution_y=1,
        band_count=1,
        band_names=["B1"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )


def test_executor_passes_change_mask_to_localization(tmp_path):
    t1_data = np.array([
        [10, 20],
        [30, 40]
    ], dtype=np.uint8)

    t2_data = np.array([
        [10, 20],
        [30, 100]
    ], dtype=np.uint8)

    t1_path = tmp_path / "t1.tif"
    t2_path = tmp_path / "t2.tif"

    create_test_raster(t1_path, t1_data)
    create_test_raster(t2_path, t2_data)

    image_a = mock_rsimage(t1_path)
    image_b = mock_rsimage(t2_path)

    registry = ToolRegistry()
    registry.register(ChangeDetectionTool())
    registry.register(ChangeLocalizationTool())

    state = AgentState(
        query="What changed?",
        inputs=[image_a, image_b],
        plan=[
            ToolCall(
                tool_name="change_detection",
                arguments={
                    "image_a": image_a,
                    "image_b": image_b,
                    "method": "absolute_difference"
                }
            ),
            ToolCall(
                tool_name="change_localization",
                arguments={
                    "mask": "computed_mask",
                    "pixel_area_sqm": 1,
                    "transform": image_a.transform
                }
            )
        ]
    )

    executor = Executor(registry)
    executor.execute(state)

    localization_result = state.results[1]

    assert localization_result.success is True
    assert localization_result.data["changed_pixel_count"] == 1