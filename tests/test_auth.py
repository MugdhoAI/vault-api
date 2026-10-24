from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_duplicate_registration_returns_conflict() -> None:
    email = f"user-{uuid4()}@example.com"
    payload = {"email": email, "password": "correct horse battery staple"}

    with TestClient(app, client=("198.51.100.11", 50000)) as client:
        first = client.post("/auth/register", json=payload)
        duplicate = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email is already registered"


def test_login_rejects_invalid_password() -> None:
    email = f"user-{uuid4()}@example.com"
    payload = {"email": email, "password": "correct horse battery staple"}

    with TestClient(app, client=("198.51.100.12", 50000)) as client:
        registered = client.post("/auth/register", json=payload)
        invalid_login = client.post(
            "/auth/token",
            json={"email": email, "password": "incorrect password"},
        )

    assert registered.status_code == 201
    assert registered.headers["cache-control"] == "no-store"
    assert invalid_login.status_code == 401
    assert invalid_login.headers["cache-control"] == "no-store"
    assert invalid_login.json()["detail"] == "Invalid credentials"


def test_secret_endpoints_reject_missing_or_invalid_tokens() -> None:
    with TestClient(app, client=("198.51.100.13", 50000)) as client:
        missing_token = client.get("/secrets")
        invalid_token = client.get(
            "/secrets",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )

    assert missing_token.status_code == 401
    assert invalid_token.status_code == 401


def test_openapi_documents_bearer_authentication() -> None:
    from app.main import app

    schema = app.openapi()
    security_schemes = schema["components"]["securitySchemes"]

    assert security_schemes["HTTPBearer"]["type"] == "http"
    assert security_schemes["HTTPBearer"]["scheme"] == "bearer"


def test_auth_endpoints_are_rate_limited() -> None:
    email = f"rate-limit-{uuid4()}@example.com"
    payload = {"email": email, "password": "incorrect-password"}

    with TestClient(app, client=("198.51.100.17", 50000)) as client:
        for _ in range(5):
            response = client.post("/auth/token", json=payload)
            assert response.status_code == 401

        limited = client.post("/auth/token", json=payload)
        assert limited.status_code == 429

def test_login_verifies_dummy_hash_for_unknown_account(monkeypatch) -> None:
    from app import main

    checked_hashes: list[str] = []

    def record_verification(password: str, hashed: str) -> bool:
        checked_hashes.append(hashed)
        return False

    monkeypatch.setattr(main, "verify_password", record_verification)

    with TestClient(app, client=("198.51.100.18", 50000)) as client:
        response = client.post(
            "/auth/token",
            json={
                "email": f"missing-{uuid4()}@example.com",
                "password": "incorrect-password",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    assert checked_hashes == [main.DUMMY_PASSWORD_HASH]

