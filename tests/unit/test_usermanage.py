import pytest

from app.ops.user_ops import create_and_commit_user, check_user_exists
from app.db.models import UserModel


def test_create_and_commit_user(db_dependency):
    email = "new@example.com"
    password = "password"
    result = create_and_commit_user(email, password, db=db_dependency)
    assert result == {"message": "User created successfully"}
    user = db_dependency.query(UserModel).filter(UserModel.email == email).first()
    assert user.email == email
    assert user.hashed_password != password # password should be hashed


# pytes parametrize
@pytest.mark.parametrize("email, expected", [
    ("user1@example.com", True),
    ("new@example.com", False)
])
def test_check_user_exists(db_dependency, email, expected):
    result = check_user_exists(email, db=db_dependency)
    assert result == expected

