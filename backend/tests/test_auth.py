from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import create_access_token
from tests.helpers import API, PASSWORD, auth, unique_email


def test_register_login_and_me(client):
    email = unique_email()

    register = client.post(
        f"{API}/auth/register",
        json={"name": "Test Student", "email": email, "password": PASSWORD},
    )

    assert register.status_code == 201

    body = register.json()

    assert body["email"] == email
    assert body["role"] == "student"
    assert "password" not in body
    assert "password_hash" not in body

    login = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": PASSWORD},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    me = client.get(f"{API}/auth/me", headers=auth(token))

    assert me.status_code == 200
    assert me.json()["email"] == email


def test_duplicate_email_is_rejected_case_insensitively(client):
    email = unique_email()

    first = client.post(
        f"{API}/auth/register",
        json={"name": "One", "email": email, "password": PASSWORD},
    )
    assert first.status_code == 201

    second = client.post(
        f"{API}/auth/register",
        json={"name": "Two", "email": email.upper(), "password": PASSWORD},
    )
    assert second.status_code == 409


def test_short_password_is_rejected_by_the_api(client):
    response = client.post(
        f"{API}/auth/register",
        json={"name": "Weak", "email": unique_email(), "password": "short"},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_cannot_register_as_admin(client):
    response = client.post(
        f"{API}/auth/register",
        json={
            "name": "Sneaky",
            "email": unique_email(),
            "password": PASSWORD,
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "student"


def test_login_with_wrong_password(client):
    email = unique_email()

    client.post(
        f"{API}/auth/register",
        json={"name": "Test", "email": email, "password": PASSWORD},
    )

    response = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_me_requires_a_token(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_garbage_token_is_401_not_500(client):
    # Regression: PyJWT errors used to escape and become a 500.
    response = client.get(f"{API}/auth/me", headers=auth("not-a-real-token"))

    assert response.status_code == 401


def test_expired_token_is_401(client):
    expired = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(f"{API}/auth/me", headers=auth(expired))

    assert response.status_code == 401


def test_token_for_a_user_that_does_not_exist_is_401(client):
    ghost_token = create_access_token(2_000_000_000)

    response = client.get(f"{API}/auth/me", headers=auth(ghost_token))

    assert response.status_code == 401
