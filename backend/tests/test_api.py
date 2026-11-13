from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health():
    assert client.get('/health').status_code==200
def test_invalid_coordinate():
    assert client.get('/cutout/0.png?ra=361&dec=0').status_code==422
