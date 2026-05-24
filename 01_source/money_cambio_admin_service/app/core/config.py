from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./money_cambio_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8125, alias="MONEY_CAMBIO_ADMIN_PORT")
    api_key_pepper: str = Field(
        default="dev-mc-admin-pepper",
        alias="MONEY_CAMBIO_ADMIN_API_KEY_PEPPER",
    )
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")
    finance_admin_base_url: str = Field(
        default="http://localhost:8123/api/v1/finance-admin",
        alias="FINANCE_ADMIN_BASE_URL",
    )
    finance_admin_sync_enabled: bool = Field(default=True, alias="FINANCE_ADMIN_SYNC_ENABLED")
    finance_admin_sync_on_start: bool = Field(default=False, alias="FINANCE_ADMIN_SYNC_ON_START")
    finance_admin_sync_after_seed: bool = Field(default=False, alias="FINANCE_ADMIN_SYNC_AFTER_SEED")
    finance_admin_timeout_sec: float = Field(default=15.0, alias="FINANCE_ADMIN_TIMEOUT_SEC")


@lru_cache
def get_settings() -> Settings:
    return Settings()
