from .models import Evidence

class EvidenceCollector:
    def __init__(self):
        self.evidence = []
        
    def add_evidence(self, ev: Evidence):
        self.evidence.append(ev)
