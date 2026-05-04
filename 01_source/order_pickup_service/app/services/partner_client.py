from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def fetch_partner_json(*, partner_id: str, timeout_sec: float | None = None) -> dict[str, Any]:
    url = f"{settings.partner_service_base_url.rstrip('/')}/partners/{partner_id}"
    to = timeout_sec if timeout_sec is not None else float(settings.backend_client_timeout_sec)
    with httpx.Client(timeout=to) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("partner response must be object")
        return data


def fetch_partner_safe(*, partner_id: str) -> dict[str, Any] | None:
    try:
        return fetch_partner_json(partner_id=partner_id)
    except Exception as exc:
        logger.warning("partner_client.fetch_failed partner_id=%s err=%s", partner_id, exc)
        return None
