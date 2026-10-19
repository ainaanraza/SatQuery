import time

import pytest
from fastapi.testclient import TestClient

from satquery.api.app import create_app
from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend


@pytest.fixture
def client():
    with TestClient(create_app(JobManager(SQLiteBackend()))) as c:
        yield c


def wait_for(client, analysis_id, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/analyze/{analysis_id}").json()
        if body["status"] not in ("queued", "running"):
            return body
        time.sleep(0.05)
    raise TimeoutError(analysis_id)


def test_analyze_is_async_and_returns_result(client):
    resp = client.post("/analyze", json={"query": "Detect change between before and after",
                                         "inputs": ["test1.tif", "demo_satellite.tif"]})
    assert resp.status_code == 202
    analysis_id = resp.json()["analysis_id"]

    body = wait_for(client, analysis_id)
    assert body["status"] == "completed"
    assert body["result"]["success"] is True
    assert body["result"]["answer"].startswith("Measured change: 0.0%")
    assert body["result"]["evidence_graph"]["edges"]
    assert body["request"]["inputs"] == ["test1.tif", "demo_satellite.tif"]


def test_unknown_analysis_is_404(client):
    assert client.get("/analyze/does-not-exist").status_code == 404


def test_request_validation(client):
    assert client.post("/analyze", json={"query": "", "inputs": ["test1.tif"]}).status_code == 422
    assert client.post("/analyze", json={"query": "q", "inputs": ["a.tif"] * 5}).status_code == 422


def test_list_analyses(client):
    ids = [client.post("/analyze", json={"query": f"q{i}", "inputs": ["test1.tif"]}).json()["analysis_id"] for i in range(2)]
    for analysis_id in ids:
        wait_for(client, analysis_id)

    listed = client.get("/analyses").json()
    assert [r["analysis_id"] for r in listed] == ids[::-1]
    assert listed[0]["query"] == "q1"
    assert "result" not in listed[0]
