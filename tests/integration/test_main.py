from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_user_endpoint_unauthorized():
    response = client.get("/user")
    assert response.status_code == 401


def test_user_endpoint_authorized(client, current_user_dependency):
    """Test the /user endpoint with authorization mocked.
    This uses the override_get_current_user fixture to simulate an authenticated user.
    """
    response = client.get("/user")
    assert response.status_code == 200
    assert response.json() == {"User": {"email": "user1@example.com", "user_id": 1}}
