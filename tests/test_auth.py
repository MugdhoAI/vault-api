from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_duplicate_registration_returns_conflict() -> None:
    email = f"user-{uuid4()}@example.com"
    payload = {"email": email, "password": "correct horse battery staple"}

    with TestClient(app) as client:
        first = client.post("/auth/register", json=payload)
        duplicate = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email is already registered"


def test_login_rejects_invalid_password() -> None:
    email = f"user-{uuid4()}@example.com"
    payload = {"email": email, "password": "correct horse battery staple"}

    with TestClient(app) as client:
        registered = client.post("/auth/register", json=payload)
        invalid_login = client.post(
            "/auth/token",
            json={"email": email, "password": "incorrect password"},
        )

    assert registered.status_code == 201
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "Invalid credentials"
