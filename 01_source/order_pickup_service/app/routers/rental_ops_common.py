"""Utilitários compartilhados entre routers rental OPS."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_value(v: Any) -> Any:
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def serialize_row(row: Any) -> dict[str, Any]:
    return {k: serialize_value(v) for k, v in dict(row).items()}
