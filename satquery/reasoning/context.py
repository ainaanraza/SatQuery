class ContextBuilder:
    def build(self, query, evidence):
        return {"query": query, "evidence": [e.id for e in evidence]}
