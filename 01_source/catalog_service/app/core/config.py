from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./catalog.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    catalog_stream_key: str = Field(default="catalog:events", alias="CATALOG_STREAM_KEY")
    product_cache_ttl_seconds: int = Field(default=300, alias="PRODUCT_CACHE_TTL_SECONDS")
    dto_version: str = Field(default="v1", alias="DTO_VERSION")


@lru_cache
def get_settings() -> Settings:
    return Settings()
