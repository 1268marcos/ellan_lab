from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class DomainHttpError(Exception):
    def __init__(self, domain: str, detail: str, *, status_code: int | None = None) -> None:
        self.domain = domain
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"{domain}: {detail}")


def fetch_json(domain: str, url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    """GET JSON de outro domínio admin; levanta DomainHttpError se indisponível."""
    timeout = get_settings().domain_http_timeout_seconds
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise DomainHttpError(domain, exc.response.text[:200] or str(exc), status_code=exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise DomainHttpError(domain, str(exc)) from exc


def fetch_items(domain: str, url: str, *, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload = fetch_json(domain, url, params=params)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return items
    return []
