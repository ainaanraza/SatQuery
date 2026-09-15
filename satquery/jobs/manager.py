import uuid

class JobManager:
    def __init__(self):
        self.jobs = {}

    def submit(self, request):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {"status": "queued", "request": request}
        return job_id
        
    def get_status(self, job_id):
        return self.jobs.get(job_id, {"status": "not_found"})
        
    def execute_sync(self, job_id):
        if job_id in self.jobs:
            req = self.jobs[job_id]["request"]
            query = req.get("query", "")
            inputs = req.get("inputs", [])
            
            try:
                from satquery.agent import SatQueryAgent
                agent = SatQueryAgent()
                response = agent.run(query=query, inputs=inputs)
                
                # Convert dataclass to dict for JSON serialization
                trace_dict = None
                if response.trace:
                    trace_dict = {
                        "detected_intent": response.trace.detected_intent,
                        "intent_confidence": response.trace.intent_confidence,
                        "tools": response.trace.tools,
                        "tool_parameters": response.trace.tool_parameters,
                        "model_used": response.trace.model_used,
                        "model_version": response.trace.model_version,
                        "confidence": response.trace.confidence,
                        "errors": response.trace.errors,
                        "warnings": response.trace.warnings,
                        "evidence_count": len(response.trace.evidence),
                    }
                result_dict = {
                    "answer": response.answer,
                    "evidence": [vars(ev) for ev in response.evidence],
                    "limitations": response.limitations,
                    "trace": trace_dict,
                    "has_evidence": response.has_evidence,
                    "evidence_count": response.evidence_count,
                    "coverage_status": response.coverage_status
                }
                
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["result"] = result_dict
            except Exception as e:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)
