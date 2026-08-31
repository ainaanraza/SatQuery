import pytest
from satquery.models.manager import ModelManager
from satquery.jobs.manager import JobManager
from satquery.storage.sqlite import SQLiteBackend
from satquery.visualization.serialization import to_geojson

def test_model_caching():
    prov1 = ModelManager.get_provider("mock")
    prov2 = ModelManager.get_provider("mock")
    assert prov1 is prov2

def test_mock_inference():
    prov = ModelManager.get_provider("mock")
    res = prov.infer({})
    assert res.provider == "mock"
    assert res.predictions["category"] == "UNKNOWN_CHANGE"

def test_job_lifecycle():
    jm = JobManager()
    jid = jm.submit({"task": "test"})
    assert jm.get_status(jid)["status"] == "queued"
    jm.execute_sync(jid)
    assert jm.get_status(jid)["status"] == "completed"

def test_sqlite_persistence():
    db = SQLiteBackend()
    db.save_analysis("a123", {"data": "test"})
    assert db.get_analysis("a123")["data"] == "test"

def test_geojson_serialization():
    geom = {"type": "Polygon", "coordinates": []}
    props = {"conf": 0.9}
    gj = to_geojson("r1", geom, props)
    assert gj["type"] == "Feature"
    assert gj["properties"]["conf"] == 0.9
