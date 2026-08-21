import pytest


async def test_register_user(async_client):
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "phone_number": "1234567890",
        "password": "strongpassword123",
        "role": 3
    }
    response = await async_client.post("/auth/register", json=user_data)


    assert response.status_code == 201


    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "user_id" in data
    assert "password" not in data


async def test_login_user(async_client):
    user_data = {
        "email": "testlogin@example.com",
        "username": "loginguy",
        "phone_number": "0987654321",
        "password": "mypassword",
        "role": 2
    }
    register_response = await async_client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    login_data = {
        "username": "testlogin@example.com",
        "password": "mypassword"
    }
    response = await async_client.post("/auth/login", data=login_data)

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testlogin@example.com"