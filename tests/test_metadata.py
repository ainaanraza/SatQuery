from satquery.inputs.metadata import detect_modality, detect_sensor

def test_detect_modality():
    assert detect_modality({"sensor": "Sentinel-1"}, []) == "sar"
    assert detect_modality({"sensor": "Sentinel-2"}, []) == "optical"
    assert detect_modality({}, []) == "unknown"

def test_detect_sensor():
    assert detect_sensor({"sensor": "Sentinel-1"}) == "Sentinel-1"
    assert detect_sensor({"sensor": "RISAT-1"}) == "RISAT"
    assert detect_sensor({}) == "unknown"
