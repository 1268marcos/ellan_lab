from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./partner.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    webhook_stream_key: str = Field(default="partner:webhooks:stream", alias="WEBHOOK_STREAM_KEY")
    webhook_consumer_group: str = Field(default="webhook_workers", alias="WEBHOOK_CONSUMER_GROUP")
    shadow_mode_enabled: bool = Field(default=False, alias="SHADOW_MODE_ENABLED")
    shadow_legacy_base_url: str = Field(default="", alias="SHADOW_LEGACY_BASE_URL")
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")


@lru_cache
def get_settings() -> Settings:
    return Settings()
