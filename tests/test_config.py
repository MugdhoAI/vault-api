import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="Production JWT_SECRET"):
        Settings(
            environment="production",
            jwt_secret="change-this-in-production",
            encryption_key=Fernet.generate_key().decode(),
        )


def test_production_requires_a_valid_fernet_key() -> None:
    with pytest.raises(ValidationError, match="Production ENCRYPTION_KEY"):
        Settings(
            environment="production",
            jwt_secret="a-unique-production-secret-that-is-long-enough",
            encryption_key="not-a-fernet-key",
        )


def test_production_accepts_configured_secrets() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="a-unique-production-secret-that-is-long-enough",
        encryption_key=Fernet.generate_key().decode(),
    )

    assert settings.environment == "production"


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="Production JWT_SECRET"):
        Settings(
            environment="production",
            jwt_secret="short-secret",
            encryption_key=Fernet.generate_key().decode(),
        )
