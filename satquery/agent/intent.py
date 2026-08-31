from dataclasses import dataclass, field
from typing import List

@dataclass
class Intent:
    name: str
    confidence: float
    required_capabilities: List[str] = field(default_factory=list)
