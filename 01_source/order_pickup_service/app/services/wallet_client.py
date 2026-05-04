from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def post_wallet_hook(*, order_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{settings.wallet_service_base_url.rstrip('/')}/internal/hooks/order-paid"
    body = {"order_id": order_id, "payload": payload or {}}
    with httpx.Client(timeout=float(settings.backend_client_timeout_sec)) as client:
        r = client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {"raw": data}


def post_wallet_hook_safe(*, order_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        return post_wallet_hook(order_id=order_id, payload=payload)
    except Exception as exc:
        logger.warning("wallet_client.hook_failed order_id=%s err=%s", order_id, exc)
        return None
