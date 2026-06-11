from app.models import UserRole
from tests.conftest import auth_headers, login


def test_register_forces_reviewer_role(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "reviewer@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == UserRole.REVIEWER.value
    assert body["email"] == "reviewer@example.com"


def test_login_returns_jwt(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client):
    client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = login(client, "me@example.com", "password123")
    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
