from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParsedQuery:
    query: str
    entities: List[str]
    operation: str
    required_inputs: List[str]
    temporal: bool = False
    cross_modal: bool = False

class QueryUnderstandingBackend:
    def parse(self, query: str) -> ParsedQuery:
        q = query.lower()
        temporal = any(kw in q for kw in ["change", "before", "after", "difference"])
        cross_modal = "sar" in q and "optical" in q
        
        op = "image_question_answering"
        req = ["image"]
        if cross_modal:
            op = "optical_sar_fusion"
            req = ["image_a", "image_b"]
        elif temporal:
            op = "change_analysis"
            req = ["image_a", "image_b"]
        elif "sensor" in q or "resolution" in q or "metadata" in q:
            op = "metadata_query"
            
        return ParsedQuery(
            query=query,
            entities=[],
            operation=op,
            required_inputs=req,
            temporal=temporal,
            cross_modal=cross_modal
        )
