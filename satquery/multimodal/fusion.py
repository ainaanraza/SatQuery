from .models import FusionResult

def fuse_deterministic(optical_rep, sar_rep):
    # Deterministic concatenation layer. Not a neural network.
    return FusionResult(
        fusion_method="deterministic_feature_stack",
        provenance_optical=optical_rep["source"] if optical_rep else None,
        provenance_sar=sar_rep["source"] if sar_rep else None,
        data="concatenated_tensor_placeholder"
    )
