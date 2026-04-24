"""Cliente HTTP para billing_fiscal_service (leitura de invoices)."""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_or_generate_invoice_id(order_id: str, *, base: str, headers: dict[str, str], timeout: int) -> str:
    by_order_url = f"{base.rstrip('/')}/internal/invoices/by-order/{order_id}"
    try:
        by_order_resp = requests.get(by_order_url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"billing_fiscal unreachable: {exc}") from exc

    if by_order_resp.status_code == 404:
        generate_url = f"{base.rstrip('/')}/internal/invoices/generate/{order_id}"
        try:
            gen_resp = requests.post(generate_url, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"billing_fiscal generate unreachable: {exc}") from exc
        if gen_resp.status_code >= 400:
            detail = (gen_resp.text or "")[:300]
            raise RuntimeError(f"billing_fiscal generate failed: status={gen_resp.status_code} detail={detail}")
        data = gen_resp.json()
    elif by_order_resp.status_code >= 400:
        raise RuntimeError(f"billing_fiscal fetch failed: status={by_order_resp.status_code}")
    else:
        data = by_order_resp.json()

    invoice_id = str(data.get("id") or "").strip()
    if not invoice_id:
        raise RuntimeError("invoice_id_missing")
    return invoice_id


def fetch_invoice_by_order_id(order_id: str) -> dict[str, Any] | None:
    """
    GET /internal/invoices/by-order/{order_id}
    Retorna dict JSON ou None se 404 / URL não configurada / erro transitório (fallback local).
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        return None

    url = f"{base.rstrip('/')}/internal/invoices/by-order/{order_id}"
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning(
            "billing_fiscal_fetch_failed order_id=%s err=%s",
            order_id,
            exc,
        )
        return None

    if resp.status_code == 404:
        return None

    if resp.status_code >= 400:
        logger.warning(
            "billing_fiscal_fetch_http order_id=%s status=%s body=%s",
            order_id,
            resp.status_code,
            (resp.text or "")[:500],
        )
        return None

    try:
        return resp.json()
    except Exception as exc:
        logger.warning("billing_fiscal_fetch_bad_json order_id=%s err=%s", order_id, exc)
        return None


def fetch_invoice_by_receipt_code(receipt_code: str) -> dict[str, Any] | None:
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        return None

    code = str(receipt_code or "").strip()
    if not code:
        return None

    url = f"{base.rstrip('/')}/internal/invoices/by-receipt-code/{code}"
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning("billing_fiscal_fetch_by_receipt_failed code=%s err=%s", code, exc)
        return None

    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        logger.warning(
            "billing_fiscal_fetch_by_receipt_http code=%s status=%s body=%s",
            code,
            resp.status_code,
            (resp.text or "")[:500],
        )
        return None
    try:
        return resp.json()
    except Exception as exc:
        logger.warning("billing_fiscal_fetch_by_receipt_bad_json code=%s err=%s", code, exc)
        return None


def resend_invoice_email_by_order_id(order_id: str) -> dict[str, Any]:
    """
    Resolve invoice por order_id e solicita reenvio de e-mail fiscal no billing.
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        raise RuntimeError("BILLING_FISCAL_SERVICE_URL not set")
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    invoice_id = _get_or_generate_invoice_id(order_id, base=base, headers=headers, timeout=timeout)
    resend_url = f"{base.rstrip('/')}/admin/fiscal/invoices/{invoice_id}/resend-email"
    try:
        resend_resp = requests.post(resend_url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"billing_fiscal resend unreachable: {exc}") from exc
    payload = {}
    try:
        payload = resend_resp.json()
    except Exception:
        payload = {"raw": (resend_resp.text or "")[:300]}
    if resend_resp.status_code >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(f"billing_fiscal resend failed: status={resend_resp.status_code} detail={detail}")
    return payload if isinstance(payload, dict) else {"ok": True}


def fetch_invoice_pdf_by_order_id(order_id: str) -> dict[str, Any]:
    """
    Resolve invoice por order_id e busca DANFE PDF stub no billing.
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        raise RuntimeError("BILLING_FISCAL_SERVICE_URL not set")
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    invoice_id = _get_or_generate_invoice_id(order_id, base=base, headers=headers, timeout=timeout)

    pdf_url = f"{base.rstrip('/')}/admin/fiscal/danfe/{invoice_id}/pdf"
    try:
        pdf_resp = requests.get(pdf_url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"billing_fiscal pdf unreachable: {exc}") from exc
    payload = {}
    try:
        payload = pdf_resp.json()
    except Exception:
        payload = {"raw": (pdf_resp.text or "")[:300]}
    if pdf_resp.status_code >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(f"billing_fiscal pdf failed: status={pdf_resp.status_code} detail={detail}")
    return payload if isinstance(payload, dict) else {"ok": True}


def force_issue_invoice_by_order_id(order_id: str) -> dict[str, Any]:
    """
    Força emissão de invoice por order_id no billing (uso operacional).
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        raise RuntimeError("BILLING_FISCAL_SERVICE_URL not set")
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 5) or 5)
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    url = (
        f"{base.rstrip('/')}/admin/fiscal/force-issue/{order_id}"
        "?allow_missing_paid_event=true"
    )
    try:
        resp = requests.post(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"billing_fiscal force-issue unreachable: {exc}") from exc
    payload = {}
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": (resp.text or "")[:300]}
    if resp.status_code >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(f"billing_fiscal force-issue failed: status={resp.status_code} detail={detail}")
    return payload if isinstance(payload, dict) else {"ok": True}


def rebuild_invoice_snapshots_for_orders(order_ids: list[str]) -> dict[str, Any]:
    """
    POST /internal/invoices/rebuild-order-snapshots
    Atualiza order_snapshot nas invoices PENDING/FAILED (e reabre DL por perfil incompleto).
    """
    base = (getattr(settings, "billing_fiscal_service_url", None) or "").strip()
    if not base:
        raise RuntimeError("BILLING_FISCAL_SERVICE_URL not set")
    timeout = int(getattr(settings, "billing_fiscal_timeout_sec", 8) or 8)
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"{base.rstrip('/')}/internal/invoices/rebuild-order-snapshots"
    try:
        resp = requests.post(url, headers=headers, json={"order_ids": order_ids}, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"billing_fiscal rebuild snapshots unreachable: {exc}") from exc
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": (resp.text or "")[:500]}
    if resp.status_code >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(f"billing_fiscal rebuild snapshots failed: status={resp.status_code} detail={detail}")
    return payload if isinstance(payload, dict) else {"ok": True}
