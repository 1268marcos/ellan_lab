from __future__ import annotations

from app.core.config import get_settings


def dto_version_header_value() -> str:
    return get_settings().dto_version
