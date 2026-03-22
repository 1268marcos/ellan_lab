# 01_source/order_pickup_service/app/services/lifecycle_domain_event_client.py
from __future__ import annotations

import os
from typing import Any

import requests

from app.core.config import settings


class LifecycleDomainEventClientError(Exception):
    pass


LIFECYCLE_SERVICE_URL = os.getenv(
    "LIFECYCLE_SERVICE_URL",
    "http://order_lifecycle_service:8010",
).rstrip("/")

TIMEOUT_SEC = int(os.getenv("LIFECYCLE_DOMAIN_EVENT_TIMEOUT_SEC", "5"))


def publish_domain_event(event_payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{LIFECYCLE_SERVICE_URL}/internal/domain-events"

    headers = {
        "X-Internal-Token": settings.internal_token,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=event_payload,
            headers=headers,
            timeout=TIMEOUT_SEC,
        )
    except requests.RequestException as exc:
        raise LifecycleDomainEventClientError(
            f"Falha ao conectar no order_lifecycle_service: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        raise LifecycleDomainEventClientError(
            f"Falha ao publicar domain event: status={response.status_code} detail={detail}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise LifecycleDomainEventClientError(
            "Resposta inválida do order_lifecycle_service ao publicar domain event."
        ) from exc
