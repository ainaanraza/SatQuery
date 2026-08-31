from dataclasses import dataclass

@dataclass
class SemanticChange:
    semantic_id: str
    category: str
    confidence: float
    status: str
    source_evidence: str
