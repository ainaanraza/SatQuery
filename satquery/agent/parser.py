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
        # Dummy rule-based parsing
        q = query.lower()
        temporal = "change" in q or "before" in q or "after" in q
        cross_modal = "sar" in q and "optical" in q
        
        op = "image_question_answering"
        req = ["image"]
        if temporal:
            op = "change_analysis"
            req = ["image_a", "image_b"]
        elif "sensor" in q or "resolution" in q:
            op = "metadata_query"
            
        return ParsedQuery(
            query=query,
            entities=[],
            operation=op,
            required_inputs=req,
            temporal=temporal,
            cross_modal=cross_modal
        )
