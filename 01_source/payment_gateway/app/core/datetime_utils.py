# 01_source/payment_gateway/app/core/datetime_utils.py
# 19/04/2026

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REGION_TIMEZONES = {
    "SP": "America/Sao_Paulo",
    "RJ": "America/Sao_Paulo",
    "MG": "America/Sao_Paulo",
    "RS": "America/Sao_Paulo",
    "BA": "America/Sao_Paulo",
    "BR": "America/Sao_Paulo",
    "PT": "Europe/Lisbon",
}


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def to_iso_utc(dt: datetime | None) -> str | None:
    dt = ensure_utc(dt)
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def normalize_datetime_like(value: Any) -> str | None:
    """
    Aceita datetime ou string ISO-ish e devolve ISO UTC com Z.
    Se não conseguir normalizar, devolve string original.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return to_iso_utc(value)

    text = str(value).strip()
    if not text:
        return None

    try:
        # Compatibilidade com strings:
        # - 2026-04-19 11:05:36.071728
        # - 2026-04-19T11:05:36.071728
        # - 2026-04-19T11:05:36.071728Z
        # - 2026-04-19T11:05:36.071728+01:00
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return to_iso_utc(parsed)
    except Exception:
        return text


def region_to_timezone(region: str | None) -> str:
    value = str(region or "").strip().upper()
    return REGION_TIMEZONES.get(value, "UTC")


