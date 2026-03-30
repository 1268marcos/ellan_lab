# 01_source/backend/runtime/app/core/config.py
import os


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


settings = Settings()