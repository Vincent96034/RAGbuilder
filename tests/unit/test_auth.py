import pytest
import time
from datetime import timedelta

from fastapi import HTTPException
from unittest.mock import patch

from app.ops.user_ops import authenticate_user, create_token, decode_token


@pytest.mark.parametrize(
    "email,password,expected",
    [
        ("user1@example.com", "password1", True),  # Successful authentication
        ("nonexistent@example.com", "password", False),  # Invalid email
        ("user1@example.com", "wrongpassword", False),  # Incorrect password
        ("", "", False),  # Empty email and password
        ("'; DROP TABLE users; --", "password", False),  # SQL Injection attempt
        ("user!@#$%^&*()_+=-{}[]:\'\,.<>?~`|\\@example.com", "password!@#$%^&*()_+=-{}[]:\'\,.<>?~`|\\", False)
    ]
)
def test_authenticate_user(email, password, expected, db_dependency):
    user = authenticate_user(email, password, db_dependency)
    if expected:
        assert user is not False
        assert user.email == email
    else:
        assert user is False


def test_create_access_token_claims(mock_env_vars):
    email = "user1@example.com"
    user_id = 1
    expires_delta = timedelta(minutes=5)
    token = create_token(email, user_id, expires_delta)
    current_user = decode_token(token)
    #payload = jwt.decode(token, encryption_secret_key, algorithms=[encryption_algorithm])
    assert current_user.email == email
    assert current_user.user_id == user_id


@pytest.mark.slow
def test_create_access_token_expiration(mock_env_vars):
    email = "user1@example.com"
    user_id = 1
    expires_delta = timedelta(seconds=1)  # Short expiration for test
    token = create_token(email, user_id, expires_delta)
    time.sleep(2)  # Wait for the token to expire
    with pytest.raises(HTTPException):
        _ = decode_token(token)



###### OLD TESTS ######

def test_authenticate_user_success(mock_db_session, mock_user):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    with patch("app.ops.user_ops.bcrypt.verify", return_value=True):
        user = authenticate_user("test@example.com", "password", mock_db_session)
        assert user.email == "test@example.com"


def test_authenticate_user_failure(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    user = authenticate_user("nonexistent@example.com", "password", mock_db_session)
    assert user is False


def test_create_access_token(mock_env_vars):
    token = create_token("test@example.com", 1, timedelta(minutes=30))
    assert token is not None