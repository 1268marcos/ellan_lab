# 01_source/order_pickup_service/app/core/config.py
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================
    # Banco / serviço
    # =========================================================

    database_url: str = Field(
        default="sqlite:////data/sqlite/order_pickup/orders.db",
        alias="DATABASE_URL",
    )

    service_name: str = Field(
        default="order_pickup_service",
        alias="SERVICE_NAME",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    app_version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )

    run_db_migrations_on_startup: bool = Field(
        default=False,
        alias="RUN_DB_MIGRATIONS_ON_STARTUP",
    )

    # =========================================================
    # Fluxo de pickup / deadlines
    # =========================================================

    pickup_window_sec: int = Field(
        default=7200,
        alias="PICKUP_WINDOW_SEC",
    )

    pickup_token_ttl_sec: int = Field(
        default=600,
        alias="PICKUP_TOKEN_TTL_SEC",
    )

    prepayment_timeout_seconds: int = Field(
        default=90,
        alias="PREPAYMENT_TIMEOUT_SECONDS",
    )

    expiry_poll_sec: int = Field(
        default=60,
        alias="EXPIRY_POLL_SEC",
    )

    lifecycle_events_poll_sec: int = Field(
        default=10,
        alias="LIFECYCLE_EVENTS_POLL_SEC",
    )

    expiry_batch_size: int = Field(
        default=100,
        alias="EXPIRY_BATCH_SIZE",
    )

    expiry_max_retries: int = Field(
        default=3,
        alias="EXPIRY_MAX_RETRIES",
    )

    expiry_enable_credit: bool = Field(
        default=False,
        alias="EXPIRY_ENABLE_CREDIT",
    )

    expiry_credit_ratio: float = Field(
        default=0.50,
        alias="EXPIRY_CREDIT_RATIO",
    )

    lifecycle_events_batch_size: int = Field(
        default=100,
        alias="LIFECYCLE_EVENTS_BATCH_SIZE",
    )

    # =========================================================
    # Backends internos / integração
    # =========================================================

    backend_sp_internal: str = Field(
        default="http://backend_sp:8000",
        alias="BACKEND_SP_INTERNAL",
    )

    backend_pt_internal: str = Field(
        default="http://backend_pt:8000",
        alias="BACKEND_PT_INTERNAL",
    )

    payment_gateway_internal: str = Field(
        default="http://payment_gateway:8000",
        alias="PAYMENT_GATEWAY_INTERNAL",
    )

    lifecycle_base_url: str = Field(
        default="http://order_lifecycle_service:8010",
        alias="ORDER_LIFECYCLE_BASE_URL",
    )

    backend_client_timeout_sec: int = Field(
        default=5,
        alias="BACKEND_CLIENT_TIMEOUT_SEC",
    )

    order_lifecycle_timeout_sec: int = Field(
        default=5,
        alias="ORDER_LIFECYCLE_TIMEOUT_SEC",
    )

    backend_price_path_template: str = Field(
        default="/catalog/skus/{sku_id}",
        alias="BACKEND_PRICE_PATH_TEMPLATE",
    )

    payment_gateway_lockers_path_template: str = Field(
        default="/lockers/{locker_id}",
        alias="PAYMENT_GATEWAY_LOCKERS_PATH_TEMPLATE",
    )

    # =========================================================
    # Segurança / auth interna
    # =========================================================

    internal_token: str = Field(
        default="dev-internal-token",
        alias="INTERNAL_TOKEN",
    )

    internal_health_token: str = Field(
        default="secret-token-123",
        alias="INTERNAL_HEALTH_TOKEN",
    )

    jwt_secret: str = Field(
        default="CHANGE_ME_IN_PROD",
        alias="JWT_SECRET",
    )

    jwt_alg: str = Field(
        default="HS256",
        alias="JWT_ALG",
    )

    jwt_access_ttl_min: int = Field(
        default=60,
        alias="JWT_ACCESS_TTL_MIN",
    )

    # =========================================================
    # QR / resgate manual
    # =========================================================

    qr_rotate_sec: int = Field(
        default=600,
        alias="QR_ROTATE_SEC",
    )

    pickup_qr_payload_version: int = Field(
        default=2,
        alias="PICKUP_QR_PAYLOAD_VERSION",
    )

    pickup_qr_secret: str = Field(
        default="",
        alias="PICKUP_QR_SECRET",
    )

    manual_redeem_max_attempts: int = Field(
        default=5,
        alias="MANUAL_REDEEM_MAX_ATTEMPTS",
    )

    manual_redeem_window_sec: int = Field(
        default=120,
        alias="MANUAL_REDEEM_WINDOW_SEC",
    )

    manual_redeem_block_sec: int = Field(
        default=300,
        alias="MANUAL_REDEEM_BLOCK_SEC",
    )

    # =========================================================
    # DEV / fallback
    # =========================================================

    dev_bypass_auth: bool = Field(
        default=False,
        alias="DEV_BYPASS_AUTH",
    )

    dev_user_id: str = Field(
        default="dev_user_1",
        alias="DEV_USER_ID",
    )

    dev_allow_unknown_sku: bool = Field(
        default=False,
        alias="DEV_ALLOW_UNKNOWN_SKU",
    )

    dev_default_price_cents: int = Field(
        default=1000,
        alias="DEV_DEFAULT_PRICE_CENTS",
    )

    dev_default_currency: str = Field(
        default="EUR",
        alias="DEV_DEFAULT_CURRENCY",
    )

    # =========================================================
    # Orders service / compat
    # =========================================================

    alloc_ttl_sec: int = Field(
        default=120,
        alias="ALLOC_TTL_SEC",
    )

    app_env: str = Field(
        default="dev",
        alias="APP_ENV",
    )

    node_env: str = Field(
        default="dev",
        alias="NODE_ENV",
    )

    # =========================================================
    # Email / SMTP
    # =========================================================

    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")

    email_host: str = Field(default="", alias="EMAIL_HOST")
    email_port: int = Field(default=465, alias="EMAIL_PORT")
    email_secure: bool = Field(default=True, alias="EMAIL_SECURE")

    email_username: str = Field(default="", alias="EMAIL_USERNAME")
    email_password: str = Field(default="", alias="EMAIL_PASSWORD")

    email_sender: str = Field(default="", alias="EMAIL_SENDER")
    email_from_name: str = Field(default="ELLAN LAB", alias="EMAIL_FROM_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()