from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from satquery.evidence.models import Evidence

@dataclass
class ToolCapabilities:
    metadata: bool = False
    raster: bool = False
    temporal: bool = False
    cross_modal: bool = False
    vision: bool = False

@dataclass
class ToolResult:
    success: bool
    tool_name: str
    data: Optional[Any] = None
    evidence: List[Evidence] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class SatQueryTool(ABC):
    name: str = "BaseTool"
    description: str = ""
    capabilities: ToolCapabilities = ToolCapabilities()

    @abstractmethod
    def execute(self, context, arguments: dict) -> ToolResult:
        pass
