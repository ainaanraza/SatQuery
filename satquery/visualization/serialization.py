import dataclasses
from datetime import date, datetime

import numpy as np


def to_geojson(region_id, geometry, properties):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties
    }


def to_jsonable(value):
    """Recursively convert agent outputs (dataclasses, tuples, numpy scalars, datetimes) to plain JSON types.

    Arrays are summarised by shape and dtype rather than serialized.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return {"array_shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, np.generic):
        return value.item()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "to_gdal"):  # affine.Affine
        return list(value)[:6]
    return str(value)
