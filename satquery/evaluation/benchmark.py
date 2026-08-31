class BenchmarkEngine:
    def __init__(self, dataset):
        self.dataset = dataset
    def run(self, model):
        return {
            "run_id": "bench_123",
            "status": "NOT_EVALUABLE",
            "metrics": {}
        }
