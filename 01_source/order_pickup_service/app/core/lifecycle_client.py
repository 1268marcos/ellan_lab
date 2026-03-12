from __future__ import annotations

from datetime import datetime, timezone, timedelta

import requests

from app.core.config import settings


class LifecycleClientError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime | None) -> datetime:
    if dt is None:
        return utc_now()

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def build_deadline_key(order_id: str) -> str:
    return f"prepayment_timeout:{order_id}"


def build_due_at(created_at: datetime | None = None) -> datetime:
    base = ensure_utc(created_at)
    return base + timedelta(seconds=settings.prepayment_timeout_seconds)


class LifecycleClient:
    def __init__(self) -> None:
        self.base_url = settings.lifecycle_base_url.rstrip("/")
        self.timeout = 10
        self.headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": settings.internal_token,
        }

    def create_prepayment_deadline(
        self,
        *,
        order_id: str,
        order_channel: str,
        region_code: str | None,
        slot_id: str | None,
        machine_id: str | None,
        created_at: datetime | None,
        extra_payload: dict | None = None,
    ) -> dict:
        payload = {
            "deadline_key": build_deadline_key(order_id),
            "order_id": order_id,
            "order_channel": order_channel,
            "deadline_type": "PREPAYMENT_TIMEOUT",
            "due_at": build_due_at(created_at).isoformat(),
            "payload": {
                "region_code": region_code,
                "slot_id": slot_id,
                "machine_id": machine_id,
                "source_service": "order_pickup_service",
                **(extra_payload or {}),
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/internal/deadlines",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LifecycleClientError(f"create deadline request failed: {exc}") from exc

        if response.status_code >= 300:
            raise LifecycleClientError(
                f"create deadline failed: status={response.status_code} body={response.text}"
            )

        return response.json()

    def cancel_prepayment_deadline(self, *, order_id: str) -> dict:
        payload = {
            "deadline_key": build_deadline_key(order_id),
        }

        try:
            response = requests.post(
                f"{self.base_url}/internal/deadlines/cancel",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LifecycleClientError(f"cancel deadline request failed: {exc}") from exc

        if response.status_code >= 300:
            raise LifecycleClientError(
                f"cancel deadline failed: status={response.status_code} body={response.text}"
            )

        return response.json()