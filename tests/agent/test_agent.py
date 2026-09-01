import pytest
from satquery.agent.agent import SatQueryAgent
from satquery.inputs.models import RSImage
from satquery.evidence.models import Evidence

def mock_rsimage(path):
    return RSImage(
        path=path,
        modality="optical",
        sensor="mock_sensor",
        acquisition_time=None,
        crs="EPSG:4326",
        bounds=(0,0,10,10),
        transform=None,
        width=100,
        height=100,
        resolution_x=1,
        resolution_y=1,
        band_count=3,
        band_names=["B1", "B2", "B3"],
        nodata=0,
        dtype="uint8",
        metadata={}
    )

def test_agent_vqa():
    agent = SatQueryAgent()
    img = mock_rsimage("test1.tif")
    response = agent.run("What is visible in this satellite image?", inputs=[img])
    assert "visible" in response.answer.lower() or "analyzed" in response.answer.lower()
    assert len(response.evidence) >= 1
    assert any("vision.answer" in ev.tool for ev in response.evidence)

def test_agent_metadata():
    agent = SatQueryAgent()
    img = mock_rsimage("test2.tif")
    response = agent.run("What sensor captured this image?", inputs=[img])
    assert "sensor" in response.answer.lower() or "mock_sensor" in response.answer.lower() or "dictionary" in str(type(response.answer)) or "mock_sensor" in str(response.answer)
    assert len(response.evidence) >= 1
