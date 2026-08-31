from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

@dataclass
class Evidence:
    source_type: str
    source: str
    tool: str
    bounds: Optional[Tuple[float, float, float, float]] = None
    crs: Optional[str] = None
    transform: Optional[Any] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
