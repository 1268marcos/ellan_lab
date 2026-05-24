from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class BillingFiscalClientError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _headers() -> dict[str, str]:
    s = get_settings()
    return {
        "X-Internal-Token": s.billing_fiscal_internal_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _base() -> str:
    return get_settings().billing_fiscal_base_url.rstrip("/")


def is_billing_fiscal_enabled() -> bool:
    return get_settings().billing_fiscal_live_enabled


def fetch_reconciliation_gaps(
    *,
    status: str = "OPEN",
    date: str | None = None,
    refresh: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    params: dict[str, str] = {"status": status, "limit": str(limit)}
    if date:
        params["date"] = date
    if refresh:
        params["refresh"] = "true"
    url = f"{_base()}/admin/fiscal/gaps"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.get(url, headers=_headers(), params=params)
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"fetch_gaps_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()


def resolve_reconciliation_gap(gap_id: str) -> dict[str, Any]:
    url = f"{_base()}/admin/fiscal/gaps/{gap_id}"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.patch(url, headers=_headers(), json={"status": "RESOLVED"})
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"resolve_gap_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()


def fetch_gap_conciliation_snapshot(*, snapshot_date: date, refresh_scan: bool = False) -> dict[str, Any]:
    params: dict[str, str] = {"date": snapshot_date.isoformat()}
    if refresh_scan:
        params["refresh"] = "true"
    url = f"{_base()}/admin/fiscal/fiscal-gap-conciliation-snapshot"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.get(url, headers=_headers(), params=params)
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"gap_snapshot_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()
