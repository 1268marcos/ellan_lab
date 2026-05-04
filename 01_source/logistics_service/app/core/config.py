from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./logistics.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/2", alias="REDIS_URL")
    order_lifecycle_base_url: str = Field(
        default="http://localhost:9100", alias="ORDER_LIFECYCLE_BASE_URL"
    )
    backend_runtime_base_url: str = Field(
        default="http://localhost:9200", alias="BACKEND_RUNTIME_BASE_URL"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
