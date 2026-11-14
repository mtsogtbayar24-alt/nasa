from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import main
from scripts.create_demo import create_demo

@pytest.fixture
def client(tmp_path, monkeypatch):
    create_demo(tmp_path/'demo')
    monkeypatch.setattr(main, 'DATA_DIR', tmp_path)
    return TestClient(main.app)


def test_health_and_provenance(client):
    result=client.get('/health')
    assert result.status_code==200
    info=result.json()
    assert info['synthetic_count']==8
    assert info['real_fits_count']==0
    assert not info['archive_connected']


def test_input_validation(client):
    assert client.get('/epochs?ra=99').status_code==422
    assert client.get('/epochs?ra=361&dec=0').status_code==422
    assert client.get('/cutout/not-here.png?ra=133.79513&dec=-7.24515').status_code==404


def test_epochs_filter_and_time_sort(client):
    r=client.get('/epochs?ra=133.79513&dec=-7.24515&fov=5')
    assert r.status_code==200
    epochs=r.json()
    assert len(epochs)==4
    assert [e['date_obs'] for e in epochs] == sorted(e['date_obs'] for e in epochs)
    assert all(e['source']=='SYNTHETIC' and not e['science_validated'] for e in epochs)


def test_cutout_difference_and_candidates(client):
    es=client.get('/epochs?ra=133.79513&dec=-7.24515&fov=5').json()
    ids=[e['id'] for e in es]
    q='ra=133.79513&dec=-7.24515&fov=5'
    raw=client.get(f'/cutout/{ids[0]}.png?{q}')
    assert raw.status_code==200
    assert raw.content[:8]==b'\x89PNG\r\n\x1a\n'
    assert raw.headers['x-data-provenance']=='SYNTHETIC'
    d=client.get(f'/difference.png?a={ids[0]}&b={ids[2]}&{q}')
    assert d.status_code==200
    assert d.content[:8]==b'\x89PNG\r\n\x1a\n'
    candidates=client.get(f'/candidates?a={ids[0]}&b={ids[2]}&{q}')
    assert candidates.status_code==200
    assert candidates.json()['candidates']
    assert 'NOT been validated' in candidates.json()['warning']
    assert client.get(f'/difference.png?a={ids[0]}&b={ids[0]}&{q}').status_code==422


def test_no_coverage(client):
    assert client.get('/epochs?ra=20&dec=-60&fov=5').json()==[]
