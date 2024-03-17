import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from http import HTTPStatus

from app.main import app
from app.schemas import CurrentUserSchema


client = TestClient(app)


@pytest.mark.parametrize("existing_user, expected_status, expected_detail", [
    (False, HTTPStatus.CREATED, "User created successfully"),
    (True, HTTPStatus.BAD_REQUEST, "User already exists"),
])
def test_create_user_route(existing_user, expected_status, expected_detail, mocker):
    # Mock dependencies
    mocker.patch('app.routes.auth.check_user_exists', return_value=existing_user)
    mock_create_user = mocker.patch(
        'app.routes.auth.create_and_commit_user', return_value=mocker.Mock(user_id="12345"))
    # create test user and send post request
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "a_secure_password"}
    response = client.post("/auth/create_user", json=user_data)
    # assert response
    assert response.status_code == expected_status
    if existing_user:
        assert response.json()["detail"] == expected_detail
    else:
        assert response.json()["message"] == expected_detail
        mock_create_user.assert_called_once_with(
            "Test", "User", "testuser@example.com", "a_secure_password")


@pytest.mark.parametrize("token_valid, expected_status, expected_response", [
    (True, HTTPStatus.OK, {"email": "user@example.com", "user_id": "user123"}),
    (False, HTTPStatus.UNAUTHORIZED, {"detail": "Invalid token."}),
])
def test_verify_token_route(token_valid, expected_status, expected_response, mocker):
    # Mock `authenticate_user` based on the token validity
    if token_valid:
        mock_user = mocker.Mock(email="user@example.com", user_id="user123")
        mocker.patch('app.routes.auth.authenticate_user', return_value=mock_user)
    else:
        mocker.patch('app.routes.auth.authenticate_user', side_effect=HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token."))
    # Define a sample token payload and send post request
    token_data = {
        "token": "valid_or_invalid_token_based_on_param"}
    response = client.post("/auth/token", json=token_data)
    # Assertions
    if token_valid:
        assert response.status_code == expected_status
        assert response.json() == expected_response


def test_delete_user_success(current_user_dependency_factory, mocker):
    # Mock get_current_user to return an authenticated user
    mock_user = CurrentUserSchema(email="user@example.com", user_id="user123")
    current_user_dependency_factory(mock_user)
    # Mock delete_and_commit_user function
    mocker.patch("app.routes.auth.delete_and_commit_user", return_value={
                 "message": "User deleted successfully"})
    response = client.delete("/auth/delete_user")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "User deleted successfully"}


def test_delete_user_unauthorized(current_user_dependency_factory, mocker):
    # Mock get_current_user to raise HTTPException for unauthorized access
    current_user_dependency_factory(None)
    response = client.delete("/auth/delete_user")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Unauthorized"}

