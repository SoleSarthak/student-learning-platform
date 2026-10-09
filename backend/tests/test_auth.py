import uuid


def test_register_user(client):

    email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    payload = {
        "name": "Test Student",
        "email": email,
        "password": "TestPassword123",
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Student"
    assert data["email"] == email
    assert data["role"] == "student"

    assert "password" not in data
    assert "password_hash" not in data


def test_login_user(client):

    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Login Test User",
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login(client):

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401