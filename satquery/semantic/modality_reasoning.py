def analyze_modality_disagreement(optical, sar):
    if optical != sar:
        return "MODALITY_DISAGREEMENT"
    return "AGREEMENT"
