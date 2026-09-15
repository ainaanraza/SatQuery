from dataclasses import dataclass, field
from typing import List, Optional
from satquery.evidence.models import Evidence

@dataclass
class ExecutionTrace:
    detected_intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    tools: List[str] = field(default_factory=list)
    tool_parameters: List[dict] = field(default_factory=list)
    model_used: Optional[str] = None
    model_version: Optional[str] = None
    evidence: List[Evidence] = field(default_factory=list)
    confidence: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
