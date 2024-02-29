import pytest

from app.schemas import CurrentUserSchema
from app.db.models import UserModel


@pytest.mark.parametrize("email,password,expected_status", [
    ("Max", "Muster", "user1@example.com", "password1", 400),
    ("Max", "Muster", "nonexistent@example.com", "password1", 201),
])
def test_create_user_success(client, db_dependency, fname, lname, email, password, expected_status):
    response = client.post(
        "/auth/create_user",
        json={"email": email, "password": password})
    assert response.status_code == expected_status
    if expected_status == 201:
        assert response.json().get("message") == "User created successfully"
    if expected_status != 201:
        assert response.json().get("detail") == "User already exists"


@pytest.mark.parametrize("email,password,expected_status,expected_key", [
    ("user1@example.com", "password1", 200, "access_token"),
    ("user1@example.com", "wrongpassword", 401, "detail"),
    ("nonexistent@example.com", "password1", 401, "detail"),
])
def test_login_for_access_token(client, db_dependency, email, password, expected_status, expected_key):
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password})
    assert response.status_code == expected_status
    assert expected_key in response.json()
    if expected_status == 200:
        assert "token_type" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"] is not None
    if expected_status != 200:
        assert response.json().get("detail") == "Incorrect email or password"
        

@pytest.mark.asyncio
async def test_delete_user_success(client, db_dependency, current_user_dependency_factory):
    email = "user_delete@example.com"
    user = CurrentUserSchema(email=email, user_id=3)
    current_user_dependency_factory(user)
    response = client.delete("/auth/delete_user")
    assert response.status_code == 200   
    assert response.json() == {"message": "User deleted successfully"}
    # Check that the user was deleted
    user = db_dependency.query(UserModel).filter_by(email=email).first()
    assert user is None

