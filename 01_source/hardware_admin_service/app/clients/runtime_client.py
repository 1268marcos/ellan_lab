from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.clients.domain_http import DomainHttpError


def _headers() -> dict[str, str]:
    return {"X-Internal-Token": get_settings().runtime_internal_token}


def list_runtime_registry_lockers() -> list[dict[str, Any]]:
    s = get_settings()
    url = f"{s.runtime_service_url}/internal/runtime/lockers"
    try:
        with httpx.Client(timeout=s.domain_http_timeout_seconds) as client:
            resp = client.get(url, headers=_headers())
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPStatusError as exc:
        raise DomainHttpError("RUNTIME", exc.response.text[:200], status_code=exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise DomainHttpError("RUNTIME", str(exc)) from exc
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return items
    return []


def trigger_runtime_central_sync(locker_id: str | None = None) -> dict[str, Any]:
    """Pede ao backend/runtime recarregar registry a partir do Postgres central."""
    s = get_settings()
    url = f"{s.runtime_service_url}/internal/runtime/sync-from-central"
    params: dict[str, Any] = {}
    if locker_id:
        params["locker_id"] = locker_id
    try:
        with httpx.Client(timeout=s.domain_http_timeout_seconds) as client:
            resp = client.post(url, params=params, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise DomainHttpError("RUNTIME", exc.response.text[:200], status_code=exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise DomainHttpError("RUNTIME", str(exc)) from exc
