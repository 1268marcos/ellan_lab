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


def recompute_fiscal_revenue_recognition(
    *,
    snapshot_date: date | None = None,
    partner_id: str | None = None,
) -> dict[str, Any]:
    """Espelha POST /admin/fiscal/revenue-recognition/recompute no billing_fiscal_service."""
    params: dict[str, str] = {}
    if snapshot_date:
        params["date_ref"] = snapshot_date.isoformat()
    url = f"{_base()}/admin/fiscal/revenue-recognition/recompute"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.post(url, headers=_headers(), params=params)
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"revenue_recompute_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()


def fetch_fiscal_gap_snapshot(*, snapshot_date: date | None = None, refresh_scan: bool = False) -> dict[str, Any]:
    params: dict[str, str] = {}
    if snapshot_date:
        params["date"] = snapshot_date.isoformat()
    if refresh_scan:
        params["refresh_scan"] = "true"
    url = f"{_base()}/admin/fiscal/fiscal-gap-conciliation-snapshot"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.get(url, headers=_headers(), params=params)
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"fiscal_gap_snapshot_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()


def issue_partner_b2b_fiscal(*, partner_id: str, invoice_id: str) -> dict[str, Any]:
    """POST /v1/partners/{partner_id}/invoices/{invoice_id}/issue-fiscal"""
    url = f"{_base()}/v1/partners/{partner_id}/invoices/{invoice_id}/issue-fiscal"
    try:
        with httpx.Client(timeout=get_settings().billing_fiscal_timeout_sec) as client:
            r = client.post(url, headers=_headers())
    except httpx.RequestError as exc:
        raise BillingFiscalClientError(f"billing_fiscal_unreachable: {exc}") from exc
    if r.status_code >= 400:
        raise BillingFiscalClientError(
            f"issue_fiscal_failed status={r.status_code}",
            status_code=r.status_code,
            payload=r.text,
        )
    return r.json()


def is_fiscal_live_enabled() -> bool:
    return get_settings().billing_fiscal_live_enabled
