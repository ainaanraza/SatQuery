from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class ModelInferenceRequest:
    prompt: str = ""
    image_paths: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelInferenceResult:
    status: str
    provider: str
    model_id: str
    model_version: str
    predictions: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    input_sources: List[str] = field(default_factory=list)
    latency: float = 0.0
    device: str = "cpu"

class MultimodalModelProvider:
    def load(self) -> None:
        pass
    def unload(self) -> None:
        pass
    def infer(self, request) -> ModelInferenceResult:
        raise NotImplementedError
    def health(self) -> dict:
        return {"status": "ok"}
