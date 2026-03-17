from typing import Any, Dict

from app.core.config import settings


def get_version() -> str:
    return settings.app_version


def get_app_info() -> Dict[str, Any]:
    return {
        "name": settings.service_name,
        "version": get_version(),
        "environment": settings.environment,
        "timestamp": None,
    }