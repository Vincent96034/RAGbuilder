import pytest
import random
import string
import logging

from fastapi.testclient import TestClient
from firebase_admin import auth

from app.main import app
from app.schemas import CreateUserRequestSchema
from app.utils.testing import create_test_token



logger = logging.getLogger(__name__)
email_tag = "999qcpnbyhsk999"


def random_string(length):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return random_string.lower()


@pytest.mark.e2e
def test_e2e_auth():
    
    client = TestClient(app)
    new_user = CreateUserRequestSchema(
        first_name="TestFirst",
        last_name="TestLast",
        email=f"testuser-{email_tag}-{random_string(10)}@testmail-{random_string(10)}.com",
        password=random_string(20))

    # Test creating a user
    response = client.post("/auth/create_user", json=new_user.__dict__)
    uid = response.json()['uid']
    assert response.status_code == 201
    assert response.json()['message'] == "User created successfully"
    
    try:
        try:
            # check if user exists in firebase: query user
            fb_user = auth.get_user_by_email(new_user.email)
        except Exception as e:
            assert False, f"User not created in Firebase: {e}"
        assert fb_user.email == new_user.email
        assert fb_user.display_name == f"{new_user.first_name} {new_user.last_name}"
        assert fb_user.uid == uid

        # try creating the same user again
        response = client.post("/auth/create_user", json=new_user.__dict__)
        assert response.status_code == 400
        assert response.json()['detail'] == "User already exists"

        # test token validation
        token = create_test_token(uid=uid)
        response = client.post("/auth/token", json={"token": token})
        assert response.status_code == 200
        assert response.json()['email'] == new_user.email
        assert response.json()['user_id'] == uid

        # test invalid token
        response = client.post("/auth/token", json={"token": "invalid_token"})
        assert response.status_code == 401

        response = client.delete(
            "/auth/delete_user",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()['message'] == "User deleted successfully"

        # check if user exists in firebase: query user
        with pytest.raises(auth.UserNotFoundError):
            _ = auth.get_user_by_email(new_user.email)
            assert True

    finally: # cleanup: delete users
        try:
            uid = auth.get_user_by_email(new_user.email).uid
            auth.delete_user(uid)
            logger.info('e2e test teardown successful')
        except Exception as e:
            logger.error(f"Failed to teardown e2e test: {e}")