from app.security import create_access_token, decode_subject, hash_password, verify_password


def test_password_hash_is_not_plaintext() -> None:
    password = "correct horse battery staple"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_round_trip() -> None:
    token = create_access_token("user@example.com")
    assert decode_subject(token) == "user@example.com"

def test_tampered_access_token_is_rejected() -> None:
    token = create_access_token("user@example.com")
    header, payload, signature = token.split(".")
    replacement = "A" if signature[0] != "A" else "B"

    assert decode_subject(f"{header}.{payload}.{replacement}{signature[1:]}") is None


def test_expired_access_token_is_rejected(monkeypatch) -> None:
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from app import security
    from app.config import Settings

    settings = Settings(jwt_secret="test-signing-secret-that-is-long-enough")
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    token = jwt.encode(
        {
            "sub": "user@example.com",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    assert security.decode_subject(token) is None

