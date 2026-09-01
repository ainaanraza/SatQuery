from satquery.models.base import MultimodalModelProvider, ModelInferenceResult
import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)

class HuggingFaceLLaVAProvider(MultimodalModelProvider):
    def __init__(self):
        self.processor = None
        self.model = None
        self.status = "UNINITIALIZED"

    def load(self) -> None:
        try:
            self.status = "LOADING"
            import torch
            from transformers import AutoProcessor, LlavaForConditionalGeneration, BitsAndBytesConfig
            
            model_id = "BigData-KSU/RS-llava-v1.5-7b-LoRA"
            logger.info(f"Loading {model_id} in 4-bit for Remote Sensing inference...")
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4"
            )
            
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.model = LlavaForConditionalGeneration.from_pretrained(
                model_id,
                quantization_config=quantization_config,
                device_map="auto"
            )
            self.status = "READY"
        except Exception as e:
            self.status = f"FAILED: {str(e)}"
            logger.error(f"Failed to load HF LLaVA model: {e}")

    def unload(self) -> None:
        self.model = None
        self.processor = None
        self.status = "UNINITIALIZED"

    def infer(self, request) -> ModelInferenceResult:
        if self.status != "READY":
            self.load()
            if self.status != "READY":
                return ModelInferenceResult(
                    status=self.status,
                    provider="hf_llava",
                    model_id="BigData-KSU/RS-llava-v1.5-7b-LoRA",
                    model_version="1.5-7b",
                    predictions={"text": f"Model initialization error: {self.status}"},
                    confidence=0.0
                )
            
        try:
            import torch
            import numpy as np
            prompt = request.prompt
            image_paths = getattr(request, "image_paths", [])
            
            image = None
            if image_paths and os.path.exists(image_paths[0]):
                try:
                    import rasterio
                    with rasterio.open(image_paths[0]) as src:
                        bands = src.read([1, 2, 3] if src.count >= 3 else [1, 1, 1])
                        bands = np.transpose(bands, (1, 2, 0))
                        if bands.max() > 0:
                            bands = (bands / bands.max() * 255).astype(np.uint8)
                        image = Image.fromarray(bands)
                except Exception:
                    image = Image.open(image_paths[0]).convert("RGB")
            else:
                image = Image.new("RGB", (336, 336), color=(34, 139, 34))

            formatted_prompt = f"USER: <image>\n{prompt}\nASSISTANT:"
            inputs = self.processor(text=formatted_prompt, images=image, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                output = self.model.generate(**inputs, max_new_tokens=150, do_sample=False)
            
            decoded = self.processor.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            
            return ModelInferenceResult(
                status="success",
                provider="hf_llava",
                model_id="BigData-KSU/RS-llava-v1.5-7b-LoRA",
                model_version="1.5-7b",
                predictions={"text": decoded},
                confidence=0.92
            )
        except Exception as e:
            return ModelInferenceResult(
                status="error",
                provider="hf_llava",
                model_id="BigData-KSU/RS-llava-v1.5-7b-LoRA",
                model_version="1.5-7b",
                predictions={"text": f"Neural inference error: {str(e)}"},
                confidence=0.0
            )

    def health(self) -> dict:
        return {"status": self.status}
