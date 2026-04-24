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

    order_pickup_service_url: str = Field(
        default="http://order_pickup_service:8003",
        alias="ORDER_PICKUP_SERVICE_URL",
    )
    order_pickup_timeout_sec: int = Field(default=5, alias="ORDER_PICKUP_TIMEOUT_SEC")

    invoice_issue_poll_sec: int = Field(default=5, alias="INVOICE_ISSUE_POLL_SEC")
    invoice_issue_batch_size: int = Field(default=50, alias="INVOICE_ISSUE_BATCH_SIZE")
    invoice_issue_max_retries: int = Field(default=5, alias="INVOICE_ISSUE_MAX_RETRIES")
    invoice_issue_base_backoff_sec: int = Field(default=15, alias="INVOICE_ISSUE_BASE_BACKOFF_SEC")
    invoice_issue_processing_timeout_sec: int = Field(
        default=180,
        alias="INVOICE_ISSUE_PROCESSING_TIMEOUT_SEC",
    )
    invoice_issue_worker_id: str = Field(default="billing_fiscal_issue_worker", alias="INVOICE_ISSUE_WORKER_ID")

    # F-3 — E-mail fiscal (SMTP opcional + fila invoice_email_outbox)
    invoice_smtp_enabled: bool = Field(default=False, alias="INVOICE_SMTP_ENABLED")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    invoice_email_max_retries: int = Field(default=5, alias="INVOICE_EMAIL_MAX_RETRIES")
    invoice_email_lock_sec: int = Field(default=120, alias="INVOICE_EMAIL_LOCK_SEC")

    # F-3 — adapters de provider real (primeiro slice: estrutura + feature flags)
    fiscal_real_provider_br_enabled: bool = Field(default=False, alias="FISCAL_REAL_PROVIDER_BR_ENABLED")
    fiscal_real_provider_pt_enabled: bool = Field(default=False, alias="FISCAL_REAL_PROVIDER_PT_ENABLED")
    fiscal_real_provider_timeout_sec: int = Field(default=8, alias="FISCAL_REAL_PROVIDER_TIMEOUT_SEC")
    fiscal_real_provider_retries: int = Field(default=2, alias="FISCAL_REAL_PROVIDER_RETRIES")
    fiscal_real_provider_base_url_br: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_BASE_URL_BR")
    fiscal_real_provider_base_url_pt: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_BASE_URL_PT")
    fiscal_real_provider_api_key_br: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_API_KEY_BR")
    fiscal_real_provider_api_key_pt: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_API_KEY_PT")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()