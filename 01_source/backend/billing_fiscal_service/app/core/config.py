# 01_source/backend/billing_fiscal_service/app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="billing_fiscal_service", alias="SERVICE_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8020, alias="PORT")
    internal_token: str = Field(default="dev-internal-token", alias="INTERNAL_TOKEN")

    postgres_host: str = Field(default="postgres_central", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="locker_central", alias="POSTGRES_DB")
    postgres_user: str = Field(default="admin", alias="POSTGRES_USER")
    postgres_password: str = Field(default="admin123", alias="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
