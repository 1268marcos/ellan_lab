# 01_source/backend/runtime/app/core/config.py
from __future__ import annotations

import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name: str = os.getenv("APP_NAME", "backend_runtime")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    internal_token: str = os.getenv("INTERNAL_TOKEN", "")

    mqtt_host: str = os.getenv("MQTT_HOST", "mqtt_broker")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))

    events_db_path: str = os.getenv("EVENTS_DB_PATH", "/data/sqlite/runtime/events.db")
    central_postgres_dsn: str = os.getenv("CENTRAL_POSTGRES_DSN", "")
    log_hash_salt: str = os.getenv("LOG_HASH_SALT", "")

    # cache curto para reduzir round-trips ao Postgres central
    runtime_registry_cache_ttl_sec: int = int(os.getenv("RUNTIME_REGISTRY_CACHE_TTL_SEC", "5"))

    # Bootstrap operacional
    runtime_apply_schema_on_startup: bool = _as_bool(
        os.getenv("RUNTIME_APPLY_SCHEMA_ON_STARTUP"),
        True,
    )
    runtime_sync_on_startup: bool = _as_bool(
        os.getenv("RUNTIME_SYNC_ON_STARTUP"),
        True,
    )
    runtime_sync_prune_missing_on_startup: bool = _as_bool(
        os.getenv("RUNTIME_SYNC_PRUNE_MISSING_ON_STARTUP"),
        False,
    )
    runtime_fail_fast_on_startup_error: bool = _as_bool(
        os.getenv("RUNTIME_FAIL_FAST_ON_STARTUP_ERROR"),
        True,
    )

    # Webhook outbound: notificar order_pickup (ou outro) imediatamente após mudança de estado do slot
    slot_state_webhook_url: str = os.getenv("SLOT_STATE_WEBHOOK_URL", "").strip()
    slot_state_webhook_secret: str = (
        os.getenv("SLOT_STATE_WEBHOOK_SECRET") or os.getenv("RUNTIME_SLOT_STATE_WEBHOOK_SECRET") or ""
    ).strip()
    slot_state_webhook_timeout_sec: float = float(os.getenv("SLOT_STATE_WEBHOOK_TIMEOUT_SEC", "2"))


settings = Settings()