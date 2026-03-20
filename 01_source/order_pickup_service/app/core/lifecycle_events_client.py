# 01_source/order_pickup_service/app/core/lifecycle_events_client.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from app.core.config import settings


class LifecycleEventsClientError(Exception):
    pass


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


class LifecycleEventsClient:
    def __init__(self) -> None:
        self.base_url = settings.lifecycle_base_url.rstrip("/")
        self.timeout = 10
        self.headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": settings.internal_token,
        }

    def list_pending_events(self, *, limit: int = 100) -> dict:
        try:
            response = requests.get(
                f"{self.base_url}/internal/events/pending",
                params={"limit": limit},
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LifecycleEventsClientError(f"list pending events request failed: {exc}") from exc

        if response.status_code >= 300:
            raise LifecycleEventsClientError(
                f"list pending events failed: status={response.status_code} body={response.text}"
            )

        return response.json()

    def ack_event(self, *, event_key: str) -> dict:
        payload = {"event_key": event_key}

        try:
            response = requests.post(
                f"{self.base_url}/internal/events/ack",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LifecycleEventsClientError(f"ack event request failed: {exc}") from exc

        if response.status_code >= 300:
            raise LifecycleEventsClientError(
                f"ack event failed: status={response.status_code} body={response.text}"
            )

        return response.json()

    def publish_pickup_event(
        self,
        *,
        event_key: str,
        event_type: str,
        occurred_at: datetime,
        order_id: str,
        pickup_id: str,
        channel: str | None = None,
        region: str | None = None,
        locker_id: str | None = None,
        machine_id: str | None = None,
        slot: str | None = None,
        operator_id: str | None = None,
        tenant_id: str | None = None,
        site_id: str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict:
        body = {
            "event_key": event_key,
            "event_type": event_type,
            "occurred_at": _to_iso(occurred_at),
            "order_id": order_id,
            "pickup_id": pickup_id,
            "channel": channel,
            "region": region,
            "locker_id": locker_id,
            "machine_id": machine_id,
            "slot": slot,
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "site_id": site_id,
            "correlation_id": correlation_id,
            "source_service": "order_pickup_service",
            "payload": payload or {},
        }

        try:
            response = requests.post(
                f"{self.base_url}/internal/pickup-events",
                json=body,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LifecycleEventsClientError(f"publish pickup event request failed: {exc}") from exc

        if response.status_code >= 300:
            raise LifecycleEventsClientError(
                f"publish pickup event failed: status={response.status_code} body={response.text}"
            )

        return response.json()