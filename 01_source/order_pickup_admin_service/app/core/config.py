from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./order_pickup_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8018, alias="ORDER_PICKUP_ADMIN_PORT")
    api_key_pepper: str = Field(default="dev-order-pickup-admin-pepper", alias="ORDER_PICKUP_ADMIN_API_KEY_PEPPER")
    seed_on_start: bool = Field(default=True, alias="SEED_ON_START")
    payments_admin_base_url: str | None = Field(
        default=None,
        alias="PAYMENTS_ADMIN_BASE_URL",
        description="Ex.: http://localhost:8126/api/v1/payments-admin — sync payment_transactions",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
