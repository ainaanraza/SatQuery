import os
import sys
import json
import logging
import argparse
from collections import defaultdict
from satquery.models.manager import ModelManager
from satquery.models.base import ModelInferenceRequest
from satquery.evaluation.metrics import exact_match, contains_match, token_f1, bleu1

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ('.tif', '.tiff', '.png', '.jpg', '.jpeg')
CAPTION_PROMPT = "Describe this remote sensing image in detail."
METRICS = {
    "exact_match": exact_match,
    "contains_match": contains_match,
    "token_f1": token_f1,
    "bleu_1": bleu1,
}

class BenchmarkEngine:
    def __init__(self, dataset_path: str, split: str = "test", max_samples: int = 50):
        self.dataset_path = dataset_path
        self.split = split
        self.max_samples = max_samples
        self.skipped = defaultdict(int)
        self._image_index = None

    def find_all_images(self, root_dir):
        """Recursively finds all raster and imagery files."""
        imgs = []
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    imgs.append(os.path.join(root, f))
        return imgs

    def find_all_jsons(self, root_dir):
        """Recursively finds all annotation JSON files."""
        jsons = []
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith('.json'):
                    jsons.append(os.path.join(root, f))
        return jsons

    def resolve_image(self, image_ref, json_dir):
        """Find an annotation's image: as given, relative to the JSON file or dataset root, or by basename anywhere in the dataset."""
        if not image_ref:
            return None
        for candidate in (image_ref, os.path.join(json_dir, image_ref), os.path.join(self.dataset_path, image_ref)):
            if os.path.isfile(candidate):
                return candidate
        if self._image_index is None:
            self._image_index = {}
            for path in self.find_all_images(self.dataset_path):
                self._image_index.setdefault(os.path.basename(path), path)
        return self._image_index.get(os.path.basename(image_ref))

    def parse_item(self, item, json_dir, fallback_id):
        """Turn one annotation record into a sample, or None (with the reason counted in self.skipped)."""
        if not isinstance(item, dict):
            return None
        question = item.get("question")
        answer = item.get("answer", item.get("ground_truth"))
        task = item.get("type") or item.get("question_type") or "vqa"

        conversations = item.get("conversations")
        if question is None and conversations:
            question = conversations[0].get("value", "")
            if answer is None and len(conversations) > 1:
                answer = conversations[1].get("value")
        if question is None and "caption" in item:
            question, answer, task = CAPTION_PROMPT, item["caption"], "caption"

        if question is None:
            return None
        if answer is None or str(answer).strip() == "":
            self.skipped["no_ground_truth"] += 1
            return None

        image_ref = item.get("image") or item.get("image_path") or item.get("image_id")
        image = self.resolve_image(image_ref, json_dir)
        if image is None:
            self.skipped["image_not_found"] += 1
            return None

        return {
            "id": item.get("question_id", item.get("id", fallback_id)),
            "image": image,
            "question": str(question).replace("<image>", "").strip(),
            "ground_truth": str(answer).strip(),
            "type": str(task),
        }

    def load_dataset(self):
        """Loads annotated VQA/caption samples (VRSBench, LLaVA-style conversations, or simple JSON lists/dicts).

        Only samples with a ground-truth answer and a locatable image are kept; there is no
        synthetic fallback, because scores without real labels are meaningless.
        """
        samples = []
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")

        for jf in sorted(self.find_all_jsons(self.dataset_path)):
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not parse {jf}: {e}")
                continue

            json_dir = os.path.dirname(jf)
            if isinstance(data, list):
                records = list(enumerate(data))
            elif isinstance(data, dict):
                records = list(data.items())
            else:
                continue
            for key, item in records:
                sample = self.parse_item(item, json_dir, fallback_id=f"{os.path.basename(jf)}:{key}")
                if sample:
                    samples.append(sample)
                if len(samples) >= self.max_samples:
                    return samples

        return samples

    def run(self, provider_name: str = "hf_llava"):
        samples = self.load_dataset()
        if not samples:
            raise ValueError(
                f"No annotated samples with images found under {self.dataset_path} "
                f"(skipped: {dict(self.skipped) or 'none'})."
            )
        provider = ModelManager.get_provider(provider_name)

        print(f"\n=======================================================")
        print(f"RUNNING REMOTE SENSING VQA EVALUATION")
        print(f"Dataset: {self.dataset_path}")
        print(f"Model Provider: {provider_name}")
        print(f"Samples to Evaluate: {len(samples)}")
        print(f"=======================================================\n")

        results = []
        totals = defaultdict(float)
        by_type = defaultdict(lambda: defaultdict(float))
        type_counts = defaultdict(int)
        inference_errors = 0
        model_id = None

        for idx, sample in enumerate(samples):
            req = ModelInferenceRequest(prompt=sample["question"], image_paths=[sample["image"]])
            res = provider.infer(req)
            model_id = model_id or res.model_id
            pred_text = res.predictions.get("text", "") if isinstance(res.predictions, dict) else ""
            if res.status != "success":
                # Failed inferences are scored as wrong answers, not dropped.
                inference_errors += 1
                pred_text = ""

            scores = {name: fn(pred_text, sample["ground_truth"]) for name, fn in METRICS.items()}
            for name, value in scores.items():
                totals[name] += value
                by_type[sample["type"]][name] += value
            type_counts[sample["type"]] += 1

            results.append({
                "sample_id": sample["id"],
                "type": sample["type"],
                "image": sample["image"],
                "question": sample["question"],
                "ground_truth": sample["ground_truth"],
                "prediction": pred_text,
                "inference_status": res.status,
                "scores": {name: round(value, 4) for name, value in scores.items()},
            })

            print(f"[{idx+1}/{len(samples)}] Q: {sample['question']}")
            print(f"      GT:   {sample['ground_truth'][:120]}")
            print(f"      Pred: {pred_text[:120]}")
            print(f"      Exact: {scores['exact_match']:.0f}  Contains: {scores['contains_match']:.0f}  F1: {scores['token_f1']:.2f}\n")

        n = len(samples)
        summary = {
            "dataset": self.dataset_path,
            "provider": provider_name,
            "model": model_id,
            "samples_evaluated": n,
            "samples_skipped": dict(self.skipped),
            "inference_errors": inference_errors,
            "metrics_percent": {name: round(100 * totals[name] / n, 2) for name in METRICS},
            "metrics_by_type_percent": {
                t: {name: round(100 * vals[name] / type_counts[t], 2) for name in METRICS}
                for t, vals in by_type.items()
            },
            "metric_definitions": {
                "exact_match": "normalized prediction equals normalized ground truth",
                "contains_match": "normalized ground truth appears as a whole phrase in the prediction",
                "token_f1": "token-overlap F1 between prediction and ground truth",
                "bleu_1": "sentence-level BLEU-1 (clipped unigram precision x brevity penalty)",
            },
            "detailed_samples": results
        }

        print(f"=======================================================")
        print(f"BENCHMARK COMPLETE ({n} samples, {inference_errors} inference errors)")
        for name, value in summary["metrics_percent"].items():
            print(f"  {name:>15}: {value:.2f}%")
        print(f"=======================================================\n")

        return summary

def main():
    parser = argparse.ArgumentParser(description="SatQuery Benchmark CLI")
    parser.add_argument("--dataset", default="/content/data/VRSBench", help="Path to evaluation dataset")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--provider", default="hf_llava", help="Model provider")
    parser.add_argument("--samples", type=int, default=20, help="Max samples to evaluate")
    parser.add_argument("--output", default="benchmark_results.json", help="Where to write detailed results")
    args = parser.parse_args()

    engine = BenchmarkEngine(dataset_path=args.dataset, split=args.split, max_samples=args.samples)
    try:
        summary = engine.run(provider_name=args.provider)
    except (FileNotFoundError, ValueError) as e:
        print(f"Benchmark aborted: {e}")
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved detailed results to {args.output}")

if __name__ == "__main__":
    main()
