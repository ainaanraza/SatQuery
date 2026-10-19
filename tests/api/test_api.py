import time

import pytest
from fastapi.testclient import TestClient

from satquery.api.app import create_app
from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend


@pytest.fixture
def upload_dir(tmp_path):
    return str(tmp_path / "uploads")


@pytest.fixture
def client(upload_dir):
    app = create_app(JobManager(SQLiteBackend()), upload_dir=upload_dir, input_roots=[], max_upload_mb=1)
    with TestClient(app) as c:
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


def upload(client, name, content):
    return client.post("/uploads", files={"file": (name, content, "application/octet-stream")})


def test_upload_then_analyze(client, upload_dir):
    with open("test1.tif", "rb") as f:
        tif = f.read()
    resp = upload(client, "S2A_MSIL2A_20230115T053211_scene.tif", tif)
    assert resp.status_code == 201
    info = resp.json()
    assert info["band_count"] == 3 and info["width"] == 512
    assert info["acquisition_time"] == "2023-01-15T05:32:11"  # kept filename carries the date
    assert info["path"].startswith(upload_dir.replace("\\", "/"))

    analysis_id = client.post("/analyze", json={"query": "What is visible?", "inputs": [info["path"]]}).json()["analysis_id"]
    assert wait_for(client, analysis_id)["result"]["success"] is True


def test_upload_rejects_bad_files(client, upload_dir):
    import os
    assert upload(client, "notes.txt", b"hello").status_code == 400
    bad = upload(client, "fake.tif", b"not really a tiff")
    assert bad.status_code == 400 and "Not a readable raster" in bad.json()["detail"]
    big = upload(client, "big.tif", b"0" * (1024 * 1024 + 1))
    assert big.status_code == 400 and "upload limit" in big.json()["detail"]
    # Rejected uploads leave nothing behind.
    assert not os.path.exists(upload_dir) or os.listdir(upload_dir) == []


def test_upload_filename_cannot_escape_upload_dir(client, upload_dir):
    with open("test1.tif", "rb") as f:
        info = upload(client, "../../evil.tif", f.read()).json()
    assert info["filename"] == "evil.tif"
    assert "/../" not in info["path"]


def test_analyze_rejects_paths_outside_allowed_roots(client, tmp_path):
    outside = str(tmp_path / "elsewhere" / "x.tif")
    resp = client.post("/analyze", json={"query": "q", "inputs": [outside]})
    assert resp.status_code == 400
    assert "outside the allowed data directories" in resp.json()["detail"]
    assert client.post("/analyze", json={"query": "q", "inputs": ["../secret.tif"]}).status_code == 400


def test_dashboard_is_served(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 307) and resp.headers["location"] == "/ui/"
    page = client.get("/ui/")
    assert page.status_code == 200 and "fileUpload" in page.text
    assert client.get("/ui/app.js").status_code == 200


def test_health_reports_provider_without_loading(client, monkeypatch):
    monkeypatch.setenv("SATQUERY_MODEL_PROVIDER", "hf_llava")
    from satquery.models.manager import ModelManager
    before = dict(ModelManager._providers)

    body = client.get("/health").json()

    assert body["model_provider"] == "hf_llava"
    assert body["model_loaded"] is ("hf_llava" in before)
    assert ModelManager._providers == before  # the health check must not load a 7B model
