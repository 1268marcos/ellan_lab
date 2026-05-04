from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./wallet.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/1", alias="REDIS_URL")
    balance_cache_ttl: int = Field(default=60, alias="BALANCE_CACHE_TTL")
    wallet_events_stream: str = Field(default="wallet:events", alias="WALLET_EVENTS_STREAM")
    divergence_max: float = Field(default=0.0001, alias="DIVERGENCE_MAX")


@lru_cache
def get_settings() -> Settings:
    return Settings()
