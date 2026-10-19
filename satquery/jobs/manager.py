import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from satquery.storage.sqlite import SQLiteBackend
from satquery.visualization.serialization import to_jsonable

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("queued", "running")


class JobManager:
    """Queues analyses, runs them on a background worker, and persists every state change.

    A single worker by default: the VLM provider holds one GPU model that is not safe
    to call concurrently.
    """

    def __init__(self, storage=None, max_workers=1):
        self.storage = storage or SQLiteBackend()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="satquery-job")
        self._agent = None

    def recover_interrupted(self):
        """Mark jobs left queued/running by a previous process as failed; returns how many."""
        stale = self.storage.list_analyses(limit=10_000, statuses=ACTIVE_STATUSES)
        for job in stale:
            self.storage.save_analysis(job["analysis_id"], {
                "status": "failed",
                "error": "Interrupted by a server restart before completion.",
            })
        return len(stale)

    def submit(self, request):
        job_id = str(uuid.uuid4())
        self.storage.save_analysis(job_id, {"status": "queued", "request": request})
        return job_id

    def start(self, job_id):
        """Run a submitted job in the background; returns its Future."""
        return self._executor.submit(self.execute_sync, job_id)

    def get_status(self, job_id):
        return self.storage.get_analysis(job_id) or {"status": "not_found"}

    def list_recent(self, limit=20):
        return self.storage.list_analyses(limit=limit)

    def execute_sync(self, job_id):
        job = self.storage.get_analysis(job_id)
        if job is None:
            return
        req = job.get("request") or {}
        self.storage.save_analysis(job_id, {"status": "running"})

        try:
            if self._agent is None:
                from satquery.agent import SatQueryAgent
                self._agent = SatQueryAgent()
            response = self._agent.run(query=req.get("query", ""), inputs=req.get("inputs", []))

            result_dict = to_jsonable({
                "success": response.success,
                "answer": response.answer,
                "answer_source": response.answer_source,
                "confidence": response.confidence,
                "errors": response.errors,
                "limitations": response.limitations,
                "evidence": response.evidence,
                "evidence_graph": response.evidence_graph,
            })
            self.storage.save_analysis(job_id, {"status": "completed", "result": result_dict})
        except Exception as e:
            logger.exception(f"Analysis {job_id} failed")
            self.storage.save_analysis(job_id, {"status": "failed", "error": f"{type(e).__name__}: {e}"})

    def shutdown(self, wait=True):
        self._executor.shutdown(wait=wait)
        if wait and hasattr(self.storage, "close"):
            self.storage.close()
