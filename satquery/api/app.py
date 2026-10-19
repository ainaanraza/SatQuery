import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from satquery.config.settings import Settings
from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend
from .uploads import UploadRejected, is_within_roots, save_upload

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

logger = logging.getLogger(__name__)

MAX_INPUTS = 4


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    inputs: List[str] = Field(..., max_length=MAX_INPUTS)


def create_app(
    job_manager: Optional[JobManager] = None,
    upload_dir: Optional[str] = None,
    input_roots: Optional[List[str]] = None,
    max_upload_mb: Optional[float] = None,
) -> FastAPI:
    """Build the API. Without `job_manager`, one backed by SQLite at Settings.DB_PATH is created at startup.

    /analyze only reads rasters inside the working directory, the upload directory, or
    `input_roots` (default Settings.INPUT_ROOTS), so a publicly tunnelled server cannot
    be used to probe arbitrary paths.
    """
    upload_dir = upload_dir or Settings.UPLOAD_DIR
    allowed_roots = [os.getcwd(), upload_dir] + list(Settings.INPUT_ROOTS if input_roots is None else input_roots)
    max_upload_bytes = int((max_upload_mb or Settings.MAX_UPLOAD_MB) * 1024 * 1024)

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
        outside = [p for p in body.inputs if not is_within_roots(p, allowed_roots)]
        if outside:
            raise HTTPException(
                status_code=400,
                detail=f"Inputs outside the allowed data directories: {', '.join(outside)}. "
                       f"Upload the file via /uploads or add its folder to SATQUERY_INPUT_ROOTS.",
            )
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

    @app.get("/health")
    def health_endpoint(request: Request):
        """Configured provider and whether it is loaded; never triggers a model load."""
        from satquery.models.manager import ModelManager
        provider = os.environ.get("SATQUERY_MODEL_PROVIDER", "mock")
        loaded = ModelManager._providers.get(provider)
        return {
            "status": "ok",
            "model_provider": provider,
            "model_loaded": loaded is not None,
            "model_status": loaded.health() if loaded is not None else None,
        }

    @app.post("/uploads", status_code=201)
    def upload_endpoint(file: UploadFile = File(...)):
        """Store one raster; the returned `path` can be used as an /analyze input."""
        os.makedirs(upload_dir, exist_ok=True)
        try:
            return save_upload(file.file, file.filename, upload_dir, max_upload_bytes)
        except UploadRejected as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            file.file.close()

    # Serve the dashboard from the API itself so it talks to its own origin (no URL to configure).
    if os.path.isdir(FRONTEND_DIR):
        app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def root():
            return RedirectResponse(url="/ui/")

    return app


app = create_app()
