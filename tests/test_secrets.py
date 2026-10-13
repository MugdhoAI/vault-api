from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def register(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_secret_lifecycle_and_user_isolation() -> None:
    password = "correct horse battery staple"
    owner_email = f"owner-{uuid4()}@example.com"
    other_email = f"other-{uuid4()}@example.com"

    with TestClient(app) as client:
        owner_token = register(client, owner_email, password)
        other_token = register(client, other_email, password)
        owner_headers = auth_header(owner_token)
        other_headers = auth_header(other_token)

        created = client.post(
            "/secrets",
            headers=owner_headers,
            json={"name": "database", "value": "initial-secret"},
        )
        assert created.status_code == 201
        secret = created.json()
        secret_id = secret["id"]
        assert secret["name"] == "database"
        assert secret["value"] == "initial-secret"

        listed = client.get("/secrets", headers=owner_headers)
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [secret_id]

        other_access = client.get(f"/secrets/{secret_id}", headers=other_headers)
        assert other_access.status_code == 404

        updated = client.patch(
            f"/secrets/{secret_id}",
            headers=owner_headers,
            json={"name": "database-prod", "value": "updated-secret"},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "database-prod"
        assert updated.json()["value"] == "updated-secret"

        fetched = client.get(f"/secrets/{secret_id}", headers=owner_headers)
        assert fetched.status_code == 200
        assert fetched.json()["value"] == "updated-secret"

        deleted = client.delete(f"/secrets/{secret_id}", headers=owner_headers)
        assert deleted.status_code == 204

        missing = client.get(f"/secrets/{secret_id}", headers=owner_headers)
        assert missing.status_code == 404



def test_secret_decryption_failure_returns_safe_error() -> None:
    from datetime import UTC, datetime

    import pytest
    from fastapi import HTTPException

    from app.main import present_secret
    from app.models import Secret

    secret = Secret(
        id=1,
        owner_id=1,
        name="example",
        value="not-a-valid-fernet-token",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(HTTPException) as error:
        present_secret(secret)

    assert error.value.status_code == 500
    assert error.value.detail == "Stored secret could not be decrypted"
    assert "not-a-valid-fernet-token" not in str(error.value.detail)
