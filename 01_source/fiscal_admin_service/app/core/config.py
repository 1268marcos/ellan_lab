from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./fiscal_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8024, alias="FISCAL_ADMIN_PORT")
    api_key_pepper: str = Field(default="dev-fiscal-admin-pepper", alias="FISCAL_ADMIN_API_KEY_PEPPER")
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")

    billing_fiscal_base_url: str = Field(
        default="http://localhost:8020",
        alias="BILLING_FISCAL_BASE_URL",
    )
    billing_fiscal_internal_token: str = Field(
        default="dev-internal-token",
        alias="BILLING_FISCAL_INTERNAL_TOKEN",
    )
    billing_fiscal_timeout_sec: float = Field(default=15.0, alias="BILLING_FISCAL_TIMEOUT_SEC")
    billing_fiscal_live_enabled: bool = Field(default=True, alias="BILLING_FISCAL_LIVE_ENABLED")


@lru_cache
def get_settings() -> Settings:
    return Settings()
