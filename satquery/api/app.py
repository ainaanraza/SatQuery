import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from satquery.config.settings import Settings
from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend

logger = logging.getLogger(__name__)

MAX_INPUTS = 4


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    inputs: List[str] = Field(..., max_length=MAX_INPUTS)


def create_app(job_manager: Optional[JobManager] = None) -> FastAPI:
    """Build the API. Without `job_manager`, one backed by SQLite at Settings.DB_PATH is created at startup."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        manager = job_manager or JobManager(SQLiteBackend(Settings.DB_PATH))
        recovered = manager.recover_interrupted()
        if recovered:
            logger.warning(f"Marked {recovered} analyses interrupted by the last shutdown as failed.")
        app.state.jobs = manager
        yield
        manager.shutdown(wait=False)

    app = FastAPI(title="SatQuery AI API", description="Phase 6 Intelligence API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/analyze", status_code=202)
    def analyze_endpoint(body: AnalyzeRequest, request: Request):
        # Returns immediately; the analysis runs on the job manager's background worker.
        jobs: JobManager = request.app.state.jobs
        job_id = jobs.submit({"query": body.query, "inputs": body.inputs})
        jobs.start(job_id)
        return {"analysis_id": job_id, "status": "queued"}

    @app.get("/analyze/{analysis_id}")
    def get_analysis_endpoint(analysis_id: str, request: Request):
        status = request.app.state.jobs.get_status(analysis_id)
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Analysis not found")
        return status

    @app.get("/analyses")
    def list_analyses_endpoint(request: Request, limit: int = 20):
        """Recent analyses, newest first, without full results."""
        records = request.app.state.jobs.list_recent(limit=max(1, min(limit, 100)))
        return [
            {
                "analysis_id": r["analysis_id"],
                "status": r["status"],
                "query": (r.get("request") or {}).get("query"),
                "inputs": (r.get("request") or {}).get("inputs"),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in records
        ]

    return app


app = create_app()
