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
        database_url="postgresql+asyncpg://vault_app:strong-password@db:5432/vault?ssl=require",
        jwt_secret="a-unique-production-secret-that-is-long-enough",
        encryption_key=Fernet.generate_key().decode(),
        rate_limit_storage_uri="redis://localhost:6379/0",
    )

    assert settings.environment == "production"


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="Production JWT_SECRET"):
        Settings(
            environment="production",
            jwt_secret="short-secret",
            encryption_key=Fernet.generate_key().decode(),
        )


def test_access_token_lifetime_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="access_token_minutes"):
        Settings(access_token_minutes=0)


def test_previous_encryption_keys_must_be_valid_fernet_keys() -> None:
    with pytest.raises(ValidationError, match="ENCRYPTION_KEY_PREVIOUS"):
        Settings(encryption_key_previous="not-a-fernet-key")


def test_production_requires_redis_for_rate_limits() -> None:
    with pytest.raises(ValidationError, match="RATE_LIMIT_STORAGE_URI"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://vault_app:strong-password@db:5432/vault?ssl=require",
            jwt_secret="a-unique-production-secret-that-is-long-enough",
            encryption_key=Fernet.generate_key().decode(),
        )


def test_production_rejects_default_database_credentials() -> None:
    with pytest.raises(ValidationError, match="local development credentials"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://vault:vault@localhost:5432/vault?ssl=require",
            jwt_secret="a-unique-production-secret-that-is-long-enough",
            encryption_key=Fernet.generate_key().decode(),
            rate_limit_storage_uri="redis://localhost:6379/0",
        )


def test_production_rejects_redis_url_without_host() -> None:
    with pytest.raises(ValidationError, match="valid Redis URL with a host"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://vault_app:strong-password@db:5432/vault?ssl=require",
            jwt_secret="a-unique-production-secret-that-is-long-enough",
            encryption_key=Fernet.generate_key().decode(),
            rate_limit_storage_uri="redis://",
        )


def test_environment_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError, match="environment"):
        Settings(environment="prod")

def test_production_requires_database_tls() -> None:
    with pytest.raises(ValidationError, match="must enable PostgreSQL TLS"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://vault_app:strong-password@db:5432/vault",
            jwt_secret="a-unique-production-secret-that-is-long-enough",
            encryption_key=Fernet.generate_key().decode(),
            rate_limit_storage_uri="redis://localhost:6379/0",
        )

