from __future__ import annotations

import requests

from app.core.config import settings


class LifecycleEventsClientError(Exception):
    pass


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