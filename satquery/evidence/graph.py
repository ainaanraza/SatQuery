from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class EvidenceNode:
    node_id: str
    node_type: str
    data: Dict
    edges: List[str] = field(default_factory=list)

class EvidenceGraph:
    """Directed provenance graph; an edge parent -> child means child was derived from parent."""

    def __init__(self):
        self.nodes = {}

    def add_node(self, node: EvidenceNode):
        self.nodes[node.node_id] = node

    def link(self, parent_id: str, child_id: str):
        if parent_id in self.nodes and child_id not in self.nodes[parent_id].edges:
            self.nodes[parent_id].edges.append(child_id)

    def parents(self, node_id: str) -> List[str]:
        return [n.node_id for n in self.nodes.values() if node_id in n.edges]

    def to_dict(self) -> dict:
        return {
            "nodes": [{"id": n.node_id, "type": n.node_type, "data": n.data} for n in self.nodes.values()],
            "edges": [{"source": n.node_id, "target": child} for n in self.nodes.values() for child in n.edges],
        }
