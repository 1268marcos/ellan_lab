from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./locker_create.db", alias="DATABASE_URL")
    service_port: int = Field(default=8015, alias="LOCKER_CREATE_PORT")
    api_key_pepper: str = Field(default="dev-locker-create-pepper", alias="LOCKER_CREATE_API_KEY_PEPPER")


@lru_cache
def get_settings() -> Settings:
    return Settings()
