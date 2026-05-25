from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./partner_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8016, alias="PARTNER_ADMIN_PORT")
    api_key_pepper: str = Field(default="dev-partner-admin-pepper", alias="PARTNER_ADMIN_API_KEY_PEPPER")
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")
    webhook_dispatch_enabled: bool = Field(default=False, alias="WEBHOOK_DISPATCH_ENABLED")
    webhook_ingress_base_url: str = Field(
        default="http://localhost:8016/api/v1/partner-admin/webhooks/ingress",
        alias="WEBHOOK_INGRESS_BASE_URL",
    )
    webhook_sandbox_fallback_url: str = Field(
        default="https://httpbin.org/post",
        alias="WEBHOOK_SANDBOX_FALLBACK_URL",
    )
    domain_http_timeout_seconds: float = Field(default=8.0, alias="DOMAIN_HTTP_TIMEOUT_SECONDS")
    payment_gateway_admin_url: str = Field(default="http://localhost:8017", alias="PAYMENT_GATEWAY_ADMIN_URL")
    marketplace_admin_url: str = Field(default="http://localhost:8119", alias="MARKETPLACE_ADMIN_URL")
    hardware_admin_url: str = Field(default="http://localhost:8025", alias="HARDWARE_ADMIN_URL")
    order_pickup_admin_url: str = Field(default="http://localhost:8018", alias="ORDER_PICKUP_ADMIN_URL")
    finance_admin_url: str = Field(default="http://localhost:8120", alias="FINANCE_ADMIN_URL")
    payments_admin_url: str = Field(default="http://localhost:8126", alias="PAYMENTS_ADMIN_URL")
    ml_admin_url: str = Field(default="http://localhost:8021", alias="ML_ADMIN_URL")
    partner_admin_base_url: str = Field(default="http://localhost:8016", alias="PARTNER_ADMIN_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
