import re
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
        # Whole-word matching, so e.g. "necessary" does not match "sar".
        words = set(re.findall(r"[a-z0-9-]+", query.lower()))
        temporal = bool(words & {"change", "changes", "changed", "before", "after", "difference", "differences"})
        cross_modal = bool(words & {"sar", "radar"}) and bool(words & {"optical", "multispectral"})

        op = "image_question_answering"
        req = ["image"]
        if cross_modal:
            op = "optical_sar_fusion"
            req = ["image_a", "image_b"]
        elif temporal:
            op = "change_analysis"
            req = ["image_a", "image_b"]
        elif words & {"sensor", "resolution", "metadata"}:
            op = "metadata_query"
            
        return ParsedQuery(
            query=query,
            entities=[],
            operation=op,
            required_inputs=req,
            temporal=temporal,
            cross_modal=cross_modal
        )
