import time

from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend


def test_sqlite_roundtrip_and_partial_update(tmp_path):
    store = SQLiteBackend(str(tmp_path / "jobs.db"))
    store.save_analysis("a1", {"status": "queued", "request": {"query": "q", "inputs": ["x.tif"]}})
    store.save_analysis("a1", {"status": "completed", "result": {"answer": "ok", "confidence": None}})

    record = store.get_analysis("a1")
    assert record["status"] == "completed"
    assert record["request"] == {"query": "q", "inputs": ["x.tif"]}  # untouched by the partial update
    assert record["result"] == {"answer": "ok", "confidence": None}
    assert record["updated_at"] >= record["created_at"]
    assert store.get_analysis("missing") is None


def test_records_survive_reopening(tmp_path):
    path = str(tmp_path / "jobs.db")
    SQLiteBackend(path).save_analysis("a1", {"status": "completed", "result": {"answer": "kept"}})
    assert SQLiteBackend(path).get_analysis("a1")["result"]["answer"] == "kept"


def test_list_newest_first_and_filter(tmp_path):
    store = SQLiteBackend()
    for i, status in enumerate(["completed", "running", "queued"]):
        store.save_analysis(f"a{i}", {"status": status})
        time.sleep(0.002)
    assert [r["analysis_id"] for r in store.list_analyses()] == ["a2", "a1", "a0"]
    assert {r["analysis_id"] for r in store.list_analyses(statuses=("queued", "running"))} == {"a1", "a2"}


def test_job_runs_in_background_and_persists():
    jobs = JobManager(SQLiteBackend())
    job_id = jobs.submit({"query": "What is visible here?", "inputs": ["test1.tif"]})
    assert jobs.get_status(job_id)["status"] == "queued"

    jobs.start(job_id).result(timeout=30)

    record = jobs.get_status(job_id)
    assert record["status"] == "completed"
    assert record["result"]["answer_source"] == "vision.answer"
    jobs.shutdown()


def test_agent_level_failure_still_completes_with_errors():
    jobs = JobManager(SQLiteBackend())
    job_id = jobs.submit({"query": "What is here?", "inputs": ["missing.tif"]})
    jobs.execute_sync(job_id)

    record = jobs.get_status(job_id)
    assert record["status"] == "completed"
    assert record["result"]["success"] is False
    assert "missing.tif" in record["result"]["errors"][0]


def test_recover_interrupted_marks_stale_jobs_failed(tmp_path):
    path = str(tmp_path / "jobs.db")
    old = SQLiteBackend(path)
    old.save_analysis("stuck", {"status": "running"})
    old.save_analysis("waiting", {"status": "queued"})
    old.save_analysis("done", {"status": "completed"})

    jobs = JobManager(SQLiteBackend(path))
    assert jobs.recover_interrupted() == 2
    assert jobs.get_status("stuck")["status"] == "failed"
    assert "restart" in jobs.get_status("waiting")["error"]
    assert jobs.get_status("done")["status"] == "completed"
