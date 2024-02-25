from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_user_endpoint_unauthorized():
    response = client.get("/user")
    assert response.status_code == 401


def test_user_endpoint_authorized(client, override_get_current_user):
    """Test the /user endpoint with authorization mocked.
    This uses the override_get_current_user fixture to simulate an authenticated user.
    """
    response = client.get("/user")
    assert response.status_code == 200
    assert response.json() == {"User": {"email": "mock@example.com", "user_id": 1}}
