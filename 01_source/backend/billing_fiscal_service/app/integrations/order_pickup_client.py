# 01_source/backend/billing_fiscal_service/app/integrations/order_pickup_client.py
from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


class OrderPickupClientError(Exception):
    pass


def get_order_snapshot(order_id: str) -> dict[str, Any]:
    url = f"{settings.order_pickup_service_url.rstrip('/')}/internal/orders/{order_id}/status"
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=settings.order_pickup_timeout_sec,
        )
    except requests.RequestException as exc:
        raise OrderPickupClientError(f"Falha ao consultar order_pickup_service: {exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise OrderPickupClientError(
            f"Consulta ao order_pickup_service falhou: status={response.status_code} detail={detail}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise OrderPickupClientError("Resposta inválida do order_pickup_service.") from exc
