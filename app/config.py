from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    app_name: str = "Vault API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://vault:vault@localhost:5432/vault"
    jwt_secret: str = "change-this-in-production"
    encryption_key: str = ""
    encryption_key_previous: str = ""
    access_token_minutes: int = Field(default=30, gt=0)
    rate_limit_storage_uri: str = "memory://"
    auth_rate_limit: str = "5/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        previous_keys = [
            key.strip()
            for key in self.encryption_key_previous.split(",")
            if key.strip()
        ]
        for key in previous_keys:
            try:
                Fernet(key.encode())
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError("ENCRYPTION_KEY_PREVIOUS must contain valid Fernet keys") from exc

        if self.environment.lower() != "production":
            return self

        if self.jwt_secret == "change-this-in-production" or len(self.jwt_secret) < 32:
            raise ValueError("Production JWT_SECRET must not use the default and must be at least 32 characters")

        try:
            Fernet(self.encryption_key.encode())
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("Production ENCRYPTION_KEY must be a valid Fernet key") from exc

        if self.encryption_key in previous_keys:
            raise ValueError("ENCRYPTION_KEY must not also appear in ENCRYPTION_KEY_PREVIOUS")

        database = make_url(self.database_url)
        if not database.username or not database.password:
            raise ValueError("Production DATABASE_URL must include database credentials")
        if database.username == "vault" and database.password == "vault":
            raise ValueError("Production DATABASE_URL must not use the local development credentials")
        ssl_mode = str(database.query.get("ssl", "")).lower()
        if ssl_mode not in {"require", "verify-ca", "verify-full"}:
            raise ValueError("Production DATABASE_URL must enable PostgreSQL TLS with ssl=require or stronger")

        rate_limit_url = urlsplit(self.rate_limit_storage_uri)
        if rate_limit_url.scheme not in {"redis", "rediss"} or not rate_limit_url.hostname:
            raise ValueError("Production RATE_LIMIT_STORAGE_URI must be a valid Redis URL with a host")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
