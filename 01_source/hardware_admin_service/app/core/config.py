from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./hardware_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8025, alias="HARDWARE_ADMIN_PORT")
    marketplace_admin_url: str = Field(
        default="http://localhost:8119",
        alias="MARKETPLACE_ADMIN_URL",
    )
    payment_gateway_admin_url: str = Field(
        default="http://localhost:8017",
        alias="PAYMENT_GATEWAY_ADMIN_URL",
    )
    order_pickup_admin_url: str = Field(
        default="http://localhost:8018",
        alias="ORDER_PICKUP_ADMIN_URL",
    )
    payments_admin_url: str = Field(
        default="http://localhost:8126",
        alias="PAYMENTS_ADMIN_URL",
    )
    finance_admin_url: str = Field(
        default="http://localhost:8123",
        alias="FINANCE_ADMIN_URL",
    )
    partner_admin_url: str = Field(
        default="http://localhost:8016",
        alias="PARTNER_ADMIN_URL",
    )
    fiscal_admin_url: str = Field(
        default="http://localhost:8024",
        alias="FISCAL_ADMIN_URL",
    )
    ml_admin_url: str = Field(
        default="http://localhost:8021",
        alias="ML_ADMIN_URL",
    )
    runtime_service_url: str = Field(
        default="http://localhost:8001",
        alias="RUNTIME_SERVICE_URL",
    )
    runtime_internal_token: str = Field(
        default="dev-runtime-internal",
        alias="RUNTIME_INTERNAL_TOKEN",
    )
    domain_http_timeout_seconds: float = Field(default=4.0, alias="DOMAIN_HTTP_TIMEOUT_SECONDS")
    webhook_dispatch_enabled: bool = Field(default=False, alias="WEBHOOK_DISPATCH_ENABLED")
    api_key_pepper: str = Field(
        default="dev-hw-admin-pepper",
        alias="HARDWARE_ADMIN_API_KEY_PEPPER",
    )
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")


@lru_cache
def get_settings() -> Settings:
    return Settings()
