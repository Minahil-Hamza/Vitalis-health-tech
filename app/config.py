"""Application settings loaded from environment variables / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration, sourced from .env."""

    database_url: str = "sqlite:///./vitalis.db"
    secret_key: str = "dev-only-secret"
    access_token_expire_hours: int = 12

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
