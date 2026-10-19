from satquery.inputs.metadata import detect_modality, detect_sensor

def test_detect_modality():
    assert detect_modality({"sensor": "Sentinel-1"}, []) == "sar"
    assert detect_modality({"sensor": "Sentinel-2"}, []) == "optical"
    assert detect_modality({}, []) == "unknown"

def test_detect_sensor():
    assert detect_sensor({"sensor": "Sentinel-1"}) == "Sentinel-1"
    assert detect_sensor({"sensor": "RISAT-1"}) == "RISAT"
    assert detect_sensor({}) == "unknown"

from datetime import datetime
from satquery.inputs.metadata import parse_datetime, detect_acquisition_time

def test_parse_datetime_formats():
    assert parse_datetime("2023-01-15T05:32:11.024Z") == datetime(2023, 1, 15, 5, 32, 11, 24000)
    assert parse_datetime("2023-01-15T10:00:00+05:30") == datetime(2023, 1, 15, 4, 30)
    assert parse_datetime("2023:01:15 10:00:00") == datetime(2023, 1, 15, 10, 0)
    assert parse_datetime("2023-01-15") == datetime(2023, 1, 15)
    assert parse_datetime("not a date") is None
    assert parse_datetime(None) is None

def test_acquisition_tag_preferred_over_filename_and_tiff_datetime():
    meta = {"TIFFTAG_DATETIME": "2024:06:01 12:00:00", "acquisition_date": "2022-03-04"}
    assert detect_acquisition_time(meta, "S2A_MSIL2A_20230115T053211_x.tif") == (datetime(2022, 3, 4), "ACQUISITION_DATE")

def test_acquisition_time_from_sentinel_and_landsat_filenames():
    assert detect_acquisition_time({}, "/d/S2A_MSIL2A_20230115T053211_N0509.tif") == (datetime(2023, 1, 15, 5, 32, 11), "filename")
    # Landsat: first date is acquisition, second is processing.
    assert detect_acquisition_time({}, "LC08_L1TP_044034_20230115_20230125_02_T1.tif") == (datetime(2023, 1, 15), "filename")

def test_tiff_datetime_is_last_resort():
    assert detect_acquisition_time({"TIFFTAG_DATETIME": "2024:06:01 12:00:00"}, "scene.tif") == (datetime(2024, 6, 1, 12), "TIFFTAG_DATETIME")
    assert detect_acquisition_time({}, "train_2956_0001.png") == (None, None)
