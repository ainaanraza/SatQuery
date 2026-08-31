from dataclasses import dataclass
from typing import Optional, Any
from satquery.inputs.models import RSImage

@dataclass
class MultimodalInput:
    optical: Optional[RSImage] = None
    sar: Optional[RSImage] = None

@dataclass
class FusionResult:
    fusion_method: str
    provenance_optical: Optional[str]
    provenance_sar: Optional[str]
    data: Any
