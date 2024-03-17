from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check_auth():
    response = client.get("/health/auth")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}

