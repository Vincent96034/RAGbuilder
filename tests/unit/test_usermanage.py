import pytest

from app.ops.user_ops import (create_and_commit_user,
                              check_user_exists, delete_and_commit_user)


def test_create_and_commit_user(db_dependency):
    response = create_and_commit_user(
        email="test_user@example.com",
        password="password123",
        db=db_dependency)
    assert response["message"] == "User created successfully"
    user_exists = check_user_exists("test_user@example.com", db_dependency)
    assert user_exists is True


@pytest.mark.parametrize("email, expected", [
    ("user1@example.com", True),
    ("new@example.com", False)
])
def test_check_user_exists(db_dependency, email, expected):
    result = check_user_exists(email, db=db_dependency)
    assert result == expected


@pytest.mark.parametrize(
    "email,creation_needed,expected_message",
    [
        ("delete_user@example.com", True, "User deleted successfully"),
        ("nonexistent_user@example.com", False, "User deleted successfully"),
    ]
)
def test_delete_and_commit_user(db_dependency, email, creation_needed, expected_message):
    # Create a user first if needed
    if creation_needed:
        create_and_commit_user(email, "password", db_dependency)
    response = delete_and_commit_user(email, db_dependency)
    assert response["message"] == expected_message
    # Verify the user no longer exists
    user_exists = check_user_exists(email, db_dependency)
    assert user_exists is False
