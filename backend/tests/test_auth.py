import pytest
import uuid


def test_register_and_login(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    email = f"testuser+{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"

    response = client.post(
        "/api/auth/token",
        data={"username": email, "password": "TestPassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"


def test_protected_endpoint_requires_auth(client):
    response = client.get("/api/history")
    assert response.status_code == 401


def test_read_current_user_returns_profile(client):
    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == email
    assert payload["name"] == "Test User"
    assert payload["id"] > 0
