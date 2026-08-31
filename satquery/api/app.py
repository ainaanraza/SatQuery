from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from satquery.jobs.manager import JobManager

app = FastAPI(title="SatQuery AI API", description="Phase 6 Intelligence API")
job_manager = JobManager()

class AnalyzeRequest(BaseModel):
    query: str
    inputs: List[str]

@app.post("/analyze")
async def analyze_endpoint(request: AnalyzeRequest):
    # Enqueue the job for async processing
    job_id = job_manager.submit({"query": request.query, "inputs": request.inputs})
    
    # In a real environment, this might trigger a background worker.
    # For testing, we'll execute it synchronously in the manager.
    job_manager.execute_sync(job_id)
    
    return {"analysis_id": job_id, "status": "queued"}

@app.get("/analyze/{analysis_id}")
async def get_analysis_endpoint(analysis_id: str):
    status = job_manager.get_status(analysis_id)
    if status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Analysis not found")
    return status
