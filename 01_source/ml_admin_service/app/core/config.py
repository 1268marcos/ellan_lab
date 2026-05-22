from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./ml_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8021, alias="ML_ADMIN_PORT")
    api_key_pepper: str = Field(default="dev-ml-admin-pepper", alias="ML_ADMIN_API_KEY_PEPPER")
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")
    webhook_dispatch_enabled: bool = Field(default=False, alias="WEBHOOK_DISPATCH_ENABLED")


@lru_cache
def get_settings() -> Settings:
    return Settings()
