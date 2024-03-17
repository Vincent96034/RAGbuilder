import pytest
from unittest.mock import patch

from firebase_admin import auth
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException

from app.ops.user_ops import (authenticate_user, get_current_user,
                              create_and_commit_user, check_user_exists, delete_and_commit_user)
from app.schemas import CurrentUserSchema


pytestmark = pytest.mark.asyncio

# Sample user data
user_id = "user123"
email = "user@example.com"
first_name = "John"
last_name = "Doe"
password = "securePassword123"


def test_authenticate_user_success(mock_auth_verify_id_token_success):
    """Test `authenticate_user` with a valid token."""
    token = "valid_token_string"
    user = authenticate_user(token)
    assert user.email == "user@example.com"
    assert user.user_id == "user123"
    mock_auth_verify_id_token_success.assert_called_once_with(token, check_revoked=True)


# Update the test to properly initialize exceptions that require arguments
@pytest.mark.parametrize("exception_constructor, token, expected_exception_message", [
    (lambda: auth.RevokedIdTokenError('Mocked message'),
     "revoked_token_string", "401: Revoked token."),
    (lambda: auth.ExpiredIdTokenError('Mocked message', 'cause'),
     "expired_token_string", "401: Expired token."),
    (lambda: auth.InvalidIdTokenError('Mocked message'),
     "invalid_token_string", "401: Invalid token."),
])
def test_authenticate_user_failure(exception_constructor, token, expected_exception_message, mocker):
    """Test `authenticate_user` with an invalid token."""
    # Create the specific exception instance using the provided constructor lambda
    specific_exception_instance = exception_constructor()
    # Mock `auth.verify_id_token` to raise the specific exception instance
    mocker.patch('app.ops.user_ops.auth.verify_id_token',
                 side_effect=specific_exception_instance)
    # Mock `raise_unauthorized_exception` to raise a standard Exception with the expected message
    mocker.patch('app.ops.exceptions.raise_unauthorized_exception',
                 side_effect=Exception(expected_exception_message))
    with pytest.raises(Exception) as exc_info:
        authenticate_user(token)
    assert str(exc_info.value) == expected_exception_message


async def test_get_current_user_valid_token(mocker):
    """Test `get_current_user` with a valid token."""
    # Mock dependencies
    valid_token = "valid_token"
    expected_user = CurrentUserSchema(email="user@example.com", user_id="user123")
    mock_auth_user = mocker.patch(
        'app.ops.user_ops.authenticate_user', return_value=expected_user)
    # Create a mock auth object
    auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
    # Call the function under test
    user = await get_current_user(auth)
    # Assertions
    assert user == expected_user
    mock_auth_user.assert_called_once_with(valid_token)


async def test_get_current_user_invalid_token(mocker):
    """Test `get_current_user` with an invalid token."""
    # Mock dependencies to raise an exception for invalid token
    invalid_token = "invalid_token"
    mocker.patch('app.ops.user_ops.authenticate_user',
                 side_effect=Exception("Invalid token."))
    # Create a mock auth object
    auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)
    # Call the function under test and expect an exception
    with pytest.raises(Exception) as exc_info:
        await get_current_user(auth)
    assert "Invalid token." in str(exc_info.value)


def test_create_and_commit_user_success(mock_firebase_user):
    """Test `create_and_commit_user` with valid user data."""
    with patch('app.ops.user_ops.auth.create_user', return_value=mock_firebase_user) as mock_create_user:
        user = create_and_commit_user(first_name, last_name, email, password)
        assert user.user_id == mock_firebase_user.uid
        assert user.email == mock_firebase_user.email
        assert user.email_verified == mock_firebase_user.email_verified
        assert user.disabled == mock_firebase_user.disabled
        assert user.display_name == mock_firebase_user.display_name
        assert user.created_at == mock_firebase_user.user_metadata.creation_timestamp
        mock_create_user.assert_called_once_with(
            email=email,
            email_verified=False,
            password=password,
            display_name=f"{first_name} {last_name}",
            disabled=False)


def test_create_and_commit_user_value_error():
    """Test `create_and_commit_user` with invalid password."""
    with patch('app.ops.user_ops.auth.create_user', side_effect=ValueError("Password must be a string with at least 6 characters.")):
        with pytest.raises(HTTPException) as exc_info:
            create_and_commit_user(first_name, last_name, email, "123")
        assert exc_info.value.status_code == 400
        assert "Password must be a string with at least 6 characters." in str(
            exc_info.value.detail)


def test_check_user_exists_true(mocker):
    """Test `check_user_exists` when the user exists."""
    # Mock `get_user_by_email` to simulate finding a user
    mocker.patch('app.ops.user_ops.auth.get_user_by_email')
    assert check_user_exists(email) is True


def test_check_user_exists_false(mocker):
    """Test `check_user_exists` when the user does not exist."""
    # Mock `get_user_by_email` to raise `UserNotFoundError` when the user does not exist
    mocker.patch('app.ops.user_ops.auth.get_user_by_email',
                 side_effect=auth.UserNotFoundError('No user'))
    email = "nonexistent@example.com"
    assert check_user_exists(email) is False


def test_delete_and_commit_user_success(mocker):
    """Test `delete_and_commit_user` with a valid email."""
    # Mock `get_user_by_email` to return a mock user object with a UID
    mock_user = mocker.Mock()
    mock_user.uid = user_id
    mocker.patch('app.ops.user_ops.auth.get_user_by_email', return_value=mock_user)
    # Mock `delete_user` to simply pass when called
    mocker.patch('app.ops.user_ops.auth.delete_user')
    result = delete_and_commit_user(email)
    # Assertions
    assert result == {"message": "User deleted successfully"}
    auth.get_user_by_email.assert_called_once_with(email)
    auth.delete_user.assert_called_once_with(mock_user.uid)


def test_delete_and_commit_user_user_not_found(mocker):
    """Test `delete_and_commit_user` when the user does not exist."""
    # Mock `get_user_by_email` to raise `UserNotFoundError` when the user does not exist
    mocker.patch('app.ops.user_ops.auth.get_user_by_email',
                 side_effect=auth.UserNotFoundError('No user'))
    # Mock `delete_user` to simply pass when called
    mocker.patch('app.ops.user_ops.auth.delete_user')
    email = "nonexistent@example.com"
    with pytest.raises(auth.UserNotFoundError):
        delete_and_commit_user(email)
    # Ensure `delete_user` was not called since the user was not found
    auth.delete_user.assert_not_called()
