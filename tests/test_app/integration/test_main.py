from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/v1")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_privacy():
    response = client.get("/v1/privacy_policy")
    assert response.status_code == 200

