class ConfidenceScorer:
    def score(self, temporal_persistence, semantic_confidence):
        if temporal_persistence > 2 and semantic_confidence > 0.8:
            return "HIGH_CONFIDENCE"
        if temporal_persistence > 0:
            return "MEDIUM_CONFIDENCE"
        return "LOW_CONFIDENCE"
