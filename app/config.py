from functools import lru_cache

from cryptography.fernet import Fernet
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vault API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://vault:vault@localhost:5432/vault"
    jwt_secret: str = "change-this-in-production"
    encryption_key: str = ""
    access_token_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment.lower() != "production":
            return self

        if self.jwt_secret == "change-this-in-production" or len(self.jwt_secret) < 32:
            raise ValueError("Production JWT_SECRET must be a unique value of at least 32 characters")

        try:
            Fernet(self.encryption_key.encode())
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("Production ENCRYPTION_KEY must be a valid Fernet key") from exc

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
