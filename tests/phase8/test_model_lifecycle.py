from satquery.models.lifecycle import ModelLifecycle

def test_lifecycle():
    life = ModelLifecycle()
    assert life.state == 'UNINITIALIZED'
    life.load()
    assert life.state == 'READY'
