from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/catalog_service"
    redis_url: str = "redis://localhost:6379/0"
    catalog_stream_key: str = "catalog:events"


settings = Settings()
