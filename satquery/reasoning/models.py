from pydantic import BaseModel
from typing import List, Optional

class ReasoningClaim(BaseModel):
    claim_id: str
    text: str
    confidence: float
    status: str
    evidence_ids: List[str]
    source_type: str
    reasoning_step: Optional[str] = None

class ReasoningResult(BaseModel):
    answer: str
    claims: List[ReasoningClaim]
    confidence: float
    evidence_ids: List[str]
    timeline: List[str]
    regions: List[str]
    warnings: List[str]
    model: str
    provider: str
