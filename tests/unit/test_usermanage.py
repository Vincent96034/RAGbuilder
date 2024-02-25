from app.ops.user_ops import create_and_commit_user, check_user_exists


def test_create_and_commit_user(mock_db_session):
    result = create_and_commit_user("new@example.com", "password", mock_db_session)
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    assert result == {"message": "User created successfully"}


def test_check_user_exists(mock_db_session, mock_user):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    exists = check_user_exists("test@example.com", mock_db_session)
    assert exists is True