from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./finance_admin.db", alias="DATABASE_URL")
    service_port: int = Field(default=8023, alias="FINANCE_ADMIN_PORT")
    api_key_pepper: str = Field(
        default="dev-finance-admin-pepper",
        alias="FINANCE_ADMIN_API_KEY_PEPPER",
    )
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
    billing_fiscal_live_enabled: bool = Field(default=False, alias="BILLING_FISCAL_LIVE_ENABLED")

    enable_finance_scheduler: bool = Field(default=True, alias="ENABLE_FINANCE_SCHEDULER")
    finance_scheduler_timezone: str = Field(default="America/Sao_Paulo", alias="FINANCE_SCHEDULER_TIMEZONE")
    finance_dunning_cron_hour: int = Field(default=8, alias="FINANCE_DUNNING_CRON_HOUR")
    finance_reconcile_cron_hour: int = Field(default=9, alias="FINANCE_RECONCILE_CRON_HOUR")
    finance_revrec_cron_hour: int = Field(default=10, alias="FINANCE_REVREC_CRON_HOUR")
    finance_fiscal_gap_cron_hour: int = Field(default=11, alias="FINANCE_FISCAL_GAP_CRON_HOUR")


@lru_cache
def get_settings() -> Settings:
    return Settings()
