
def test_create_user_success(client, override_get_db):
    response = client.post("/auth/create_user", json={"email": "test@example.com", "password": "password"})
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}


def test_login_for_access_token_success(client, override_get_db):
    # Assuming the user "test@example.com" was successfully created in the previous test
    response = client.post("/auth/token", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_delete_user_success(client, override_get_db, override_get_current_user):
    response = client.post("/auth/delete_user")
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted successfully"}
