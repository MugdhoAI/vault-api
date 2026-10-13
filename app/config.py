from functools import lru_cache

from cryptography.fernet import Fernet
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vault API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://vault:vault@localhost:5432/vault"
    jwt_secret: str = "change-this-in-production"
    encryption_key: str = ""
    encryption_key_previous: str = ""
    access_token_minutes: int = Field(default=30, gt=0)

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

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
