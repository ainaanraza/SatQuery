from dataclasses import dataclass, field
from typing import List, Optional
from satquery.inputs.models import RSImage
from satquery.evidence.models import Evidence
from satquery.tools.base import ToolResult
from .parser import ParsedQuery
from .intent import Intent

@dataclass
class ResultRef:
    """Placeholder for a value produced by an earlier tool in the plan.

    Resolved by the Executor from the latest successful result of `tool_name`;
    `key` selects one field of that result's data (None means the whole data).
    """
    tool_name: str
    key: Optional[str] = None

@dataclass
class ToolCall:
    tool_name: str
    arguments: dict

@dataclass
class AgentState:
    query: str
    parsed_query: Optional[ParsedQuery] = None
    intent: Optional[Intent] = None
    inputs: List[RSImage] = field(default_factory=list)
    plan: List[ToolCall] = field(default_factory=list)
    results: List[ToolResult] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    final_answer: Optional[str] = None
