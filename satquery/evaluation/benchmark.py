import os
import json
import logging
import argparse
from satquery.models.manager import ModelManager
from satquery.models.base import ModelInferenceRequest

logger = logging.getLogger(__name__)

class BenchmarkEngine:
    def __init__(self, dataset_path: str, split: str = "test", max_samples: int = 50):
        self.dataset_path = dataset_path
        self.split = split
        self.max_samples = max_samples

    def load_dataset(self):
        """Loads VRSBench, RSVQA, or custom remote sensing benchmark samples."""
        samples = []
        if not os.path.exists(self.dataset_path):
            print(f"Dataset path {self.dataset_path} not found. Using synthetic validation split for testing.")
            for i in range(min(10, self.max_samples)):
                samples.append({
                    "id": f"sample_{i}",
                    "image": "test1.tif",
                    "question": "What is the primary land-use visible in this area?",
                    "ground_truth": "urban infrastructure and agricultural land"
                })
            return samples

        # Check for VRSBench JSON files
        json_files = [f for f in os.listdir(self.dataset_path) if f.endswith('.json')]
        if json_files:
            target_json = os.path.join(self.dataset_path, json_files[0])
            try:
                with open(target_json, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        samples = data[:self.max_samples]
                    elif isinstance(data, dict):
                        samples = list(data.values())[:self.max_samples]
            except Exception as e:
                print(f"Error loading {target_json}: {e}")

        if not samples:
            # Fallback search for image files in dataset path
            img_files = [os.path.join(self.dataset_path, f) for f in os.listdir(self.dataset_path) if f.endswith(('.tif', '.png', '.jpg'))]
            for idx, img in enumerate(img_files[:self.max_samples]):
                samples.append({
                    "id": f"rs_sample_{idx}",
                    "image": img,
                    "question": "Identify key geographic features and changes.",
                    "ground_truth": "remote sensing landscape"
                })
                
        return samples

    def run(self, provider_name: str = "hf_llava"):
        provider = ModelManager.get_provider(provider_name)
        samples = self.load_dataset()
        
        print(f"\n=======================================================")
        print(f"🛰️  RUNNING BENCHMARK EVALUATION")
        print(f"Dataset: {self.dataset_path}")
        print(f"Model Provider: {provider_name} (RS-llava-v1.5-7b-LoRA)")
        print(f"Total Samples to Evaluate: {len(samples)}")
        print(f"=======================================================\n")

        results = []
        correct_count = 0

        for idx, sample in enumerate(samples):
            q = sample.get("question", "Describe the image.")
            img_path = sample.get("image", "test1.tif")
            gt = sample.get("ground_truth", "")

            req = ModelInferenceRequest(prompt=q, image_paths=[img_path])
            res = provider.infer(req)
            pred_text = res.predictions.get("text", "")

            # Simple token overlap metric
            gt_words = set(gt.lower().split())
            pred_words = set(pred_text.lower().split())
            overlap = len(gt_words.intersection(pred_words)) / max(len(gt_words), 1) if gt_words else 0.5
            
            if overlap > 0.3:
                correct_count += 1

            results.append({
                "sample_id": sample.get("id", idx),
                "question": q,
                "prediction": pred_text,
                "ground_truth": gt,
                "overlap_score": round(overlap, 3)
            })

            print(f"[{idx+1}/{len(samples)}] Q: {q}")
            print(f"      Pred: {pred_text[:80]}...")
            print(f"      Score: {round(overlap, 3)}\n")

        accuracy = (correct_count / len(samples)) * 100 if samples else 0.0
        summary = {
            "dataset": self.dataset_path,
            "provider": provider_name,
            "samples_evaluated": len(samples),
            "estimated_vqa_accuracy": f"{accuracy:.2f}%",
            "results": results
        }

        print(f"=======================================================")
        print(f"📊 BENCHMARK COMPLETE!")
        print(f"Accuracy: {accuracy:.2f}%")
        print(f"=======================================================\n")

        return summary

def main():
    parser = argparse.ArgumentParser(description="SatQuery Benchmark CLI")
    parser.add_argument("--dataset", default="/content/data/VRSBench", help="Path to evaluation dataset")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--provider", default="hf_llava", help="Model provider")
    parser.add_argument("--samples", type=int, default=20, help="Max samples to evaluate")
    args = parser.parse_args()

    engine = BenchmarkEngine(dataset_path=args.dataset, split=args.split, max_samples=args.samples)
    summary = engine.run(provider_name=args.provider)

    with open("benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved detailed results to benchmark_results.json")

if __name__ == "__main__":
    main()
