from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite:////data/sqlite/order_pickup/orders.db", # anteriormente "sqlite:///./data/orders.db",  
        alias="DATABASE_URL",
    )

    pickup_window_sec: int = Field(
        default=7200,
        alias="PICKUP_WINDOW_SEC",
    )

    pickup_token_ttl_sec: int = Field(
        default=600,
        alias="PICKUP_TOKEN_TTL_SEC",
    )

    prepayment_timeout_seconds: int = Field(
        default=90, # 1 minuto e 30 segundos
        alias="PREPAYMENT_TIMEOUT_SECONDS",
    )

    service_name: str = Field(
        default="order_pickup_service",
        alias="SERVICE_NAME",
    )

    backend_sp_internal: str = Field(
        default="http://backend_sp:8000",
        alias="BACKEND_SP_INTERNAL",
    )

    backend_pt_internal: str = Field(
        default="http://backend_pt:8000",
        alias="BACKEND_PT_INTERNAL",
    )

    lifecycle_base_url: str = Field(
        default="http://order_lifecycle_service:8010",
        alias="ORDER_LIFECYCLE_BASE_URL",
    )

    internal_token: str = Field(
        default="dev-internal-token",
        alias="INTERNAL_TOKEN",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()