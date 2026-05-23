from __future__ import annotations

from app.core.config import get_settings


def health_payload() -> dict:
    return {
        "status": "ok",
        "service": "finance-admin-service",
        "port": get_settings().service_port,
    }
