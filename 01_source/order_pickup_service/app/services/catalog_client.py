from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def fetch_product_json(*, sku_id: str, timeout_sec: float | None = None) -> dict[str, Any]:
    url = f"{settings.catalog_service_base_url.rstrip('/')}/api/v1/products/{sku_id}"
    to = timeout_sec if timeout_sec is not None else float(settings.backend_client_timeout_sec)
    with httpx.Client(timeout=to) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("catalog response must be object")
        return data


def fetch_product_safe(*, sku_id: str) -> dict[str, Any] | None:
    try:
        return fetch_product_json(sku_id=sku_id)
    except Exception as exc:
        logger.warning("catalog_client.fetch_failed sku_id=%s err=%s", sku_id, exc)
        return None
