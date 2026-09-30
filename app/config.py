from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vault API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://vault:vault@localhost:5432/vault"
    jwt_secret: str = "change-this-in-production"
    encryption_key: str = ""
    access_token_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
