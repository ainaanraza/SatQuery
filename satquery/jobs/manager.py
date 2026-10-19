import uuid
from satquery.visualization.serialization import to_jsonable

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
                
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["result"] = result_dict
            except Exception as e:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)
