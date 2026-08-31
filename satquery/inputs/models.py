from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Tuple, Dict, Literal

@dataclass
class RSImage:
    path: str
    modality: Optional[str]
    sensor: Optional[str]
    acquisition_time: Optional[datetime]
    crs: Optional[str]
    bounds: Optional[Tuple[float, float, float, float]]
    transform: Optional[Any]
    width: int
    height: int
    resolution_x: Optional[float]
    resolution_y: Optional[float]
    band_count: int
    band_names: List[str]
    nodata: Optional[float]
    dtype: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RSImagePair:
    first: RSImage
    second: RSImage
    relation: Literal["temporal", "cross_modal", "unknown"]
    spatially_compatible: bool
    aligned: bool
    overlap_bounds: Optional[Tuple[float, float, float, float]]
    validation_messages: List[str] = field(default_factory=list)
