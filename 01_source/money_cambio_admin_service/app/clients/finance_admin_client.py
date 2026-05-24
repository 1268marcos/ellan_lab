from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class FinanceAdminClientError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class FinanceAdminClient:
    """Cliente REST para finance-admin locker-network-catalog."""

    def __init__(self, base_url: str | None = None, timeout_sec: float | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.finance_admin_base_url).rstrip("/")
        self.timeout = timeout_sec if timeout_sec is not None else settings.finance_admin_timeout_sec

    def _get(self, path: str, *, params: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params or {})
        except httpx.RequestError as exc:
            raise FinanceAdminClientError(f"finance_admin_unreachable: {exc}") from exc
        if resp.status_code >= 400:
            raise FinanceAdminClientError(
                f"finance_admin_http_{resp.status_code}",
                status_code=resp.status_code,
            )
        return resp.json()

    def _post(self, path: str, *, params: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, params=params or {})
        except httpx.RequestError as exc:
            raise FinanceAdminClientError(f"finance_admin_unreachable: {exc}") from exc
        if resp.status_code >= 400:
            raise FinanceAdminClientError(
                f"finance_admin_http_{resp.status_code}",
                status_code=resp.status_code,
            )
        return resp.json()

    def trigger_catalog_sync(self, *, create_partners: bool = False, create_plans: bool = False) -> dict:
        return self._post(
            "/locker-network-catalog/sync",
            params={
                "create_partners": str(create_partners).lower(),
                "create_plans": str(create_plans).lower(),
            },
        )

    def fetch_catalog(self) -> list[dict]:
        data = self._get("/locker-network-catalog")
        return list(data.get("items") or [])

    def fetch_segments(self) -> list[dict]:
        data = self._get("/locker-network-catalog/segments")
        return list(data.get("items") or [])

    def fetch_relations(self) -> list[dict]:
        data = self._get("/locker-network-catalog/relations")
        return list(data.get("items") or [])


def parse_regions_json(raw: str | list | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        parsed = json.loads(raw or "[]")
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
