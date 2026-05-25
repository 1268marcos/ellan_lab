from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./privacy_compliance_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8022, alias="PRIVACY_COMPLIANCE_ADMIN_PORT")
    api_key_pepper: str = Field(
        default="dev-privacy-admin-pepper",
        alias="PRIVACY_COMPLIANCE_ADMIN_API_KEY_PEPPER",
    )
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")
    partner_admin_base_url: str = Field(
        default="http://localhost:8016/api/v1/partner-admin",
        alias="PARTNER_ADMIN_BASE_URL",
    )
    marketplace_admin_base_url: str = Field(
        default="http://localhost:8119/api/v1/marketplace-admin",
        alias="MARKETPLACE_ADMIN_BASE_URL",
    )
    webhook_dispatch_timeout_sec: float = Field(default=5.0, alias="PRIVACY_WEBHOOK_TIMEOUT_SEC")


@lru_cache
def get_settings() -> Settings:
    return Settings()
