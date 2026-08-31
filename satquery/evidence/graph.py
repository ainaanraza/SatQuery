from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class EvidenceNode:
    node_id: str
    node_type: str
    data: Dict
    edges: List[str] = field(default_factory=list)

class EvidenceGraph:
    def __init__(self):
        self.nodes = {}
    
    def add_node(self, node: EvidenceNode):
        self.nodes[node.node_id] = node
        
    def link(self, parent_id: str, child_id: str):
        if parent_id in self.nodes:
            self.nodes[parent_id].edges.append(child_id)
