from unittest.mock import patch
from app.ops.user_ops import authenticate_user, create_access_token
from datetime import timedelta


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
    token = create_access_token("test@example.com", 1, timedelta(minutes=30))
    assert token is not None