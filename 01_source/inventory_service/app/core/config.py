from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./inventory.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    events_stream: str = Field(default="inventory:events", alias="EVENTS_STREAM")
    dlq_stream: str = Field(default="inventory:dlq", alias="DLQ_STREAM")
    consumer_group: str = Field(default="inventory_workers", alias="CONSUMER_GROUP")
    kafka_bootstrap: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP")
    schema_registry_url: str = Field(default="http://localhost:8081", alias="SCHEMA_REGISTRY_URL")
    mtls_ca_file: str = Field(default="", alias="MTLS_CA_FILE")
    mtls_cert_file: str = Field(default="", alias="MTLS_CERT_FILE")
    mtls_key_file: str = Field(default="", alias="MTLS_KEY_FILE")


@lru_cache
def get_settings() -> Settings:
    return Settings()
