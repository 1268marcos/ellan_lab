"""Cliente HTTP para billing_fiscal_service (leitura de invoices)."""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def fetch_invoice_by_order_id(order_id: str) -> dict[str, Any] | None:
    """
    GET /internal/invoices/by-order/{order_id}
    Retorna dict JSON ou None se 404 / URL não configurada / erro transitório (fallback local).
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        return None

    url = f"{base.rstrip('/')}/internal/invoices/by-order/{order_id}"
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning(
            "billing_fiscal_fetch_failed order_id=%s err=%s",
            order_id,
            exc,
        )
        return None

    if resp.status_code == 404:
        return None

    if resp.status_code >= 400:
        logger.warning(
            "billing_fiscal_fetch_http order_id=%s status=%s body=%s",
            order_id,
            resp.status_code,
            (resp.text or "")[:500],
        )
        return None

    try:
        return resp.json()
    except Exception as exc:
        logger.warning("billing_fiscal_fetch_bad_json order_id=%s err=%s", order_id, exc)
        return None
