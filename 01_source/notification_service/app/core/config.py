from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./notification.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/2", alias="REDIS_URL")
    rate_limit_per_hour: int = Field(default=10, alias="RATE_LIMIT_PER_HOUR")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")


@lru_cache
def get_settings() -> Settings:
    return Settings()
