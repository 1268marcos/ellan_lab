"""F3B-STUB-01 — simulador AT Portugal (stub dedicado) com fachada REST vs SOAP.

Objetivo: exercitar integração e testes sem AT real; contrato estável alinhado ao
`fiscal_provider_contract` (campos usados por `normalize_issue_response` / cancel PT).

Não persiste em BD; estado em memória com idempotência por chave (processo local).
"""
from __future__ import annotations

import base64
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

_LOCK = threading.Lock()
_ISSUE_BY_IDEMPOTENCY: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_wire_mode(raw: str | None) -> str:
    m = str(raw or "rest").strip().lower()
    if m in ("soap", "soap12", "xml"):
        return "soap"
    return "rest"


def _derive_idempotency_key(payload: dict) -> str:
    explicit = str(payload.get("idempotency_key") or "").strip()
    if explicit:
        return explicit
    invoice_id = str(payload.get("invoice_id") or "").strip()
    order_id = str(payload.get("order_id") or "").strip()
    access_key = str(payload.get("access_key") or "").strip()
    joined = "|".join((invoice_id, order_id, access_key))
    if joined.strip("|"):
        return joined
    raise ValueError("at_pt_stub_issue_requires_idempotency_or_ids")


def _wire_envelope(*, wire_mode: str, operation: str, canonical: dict[str, Any]) -> dict[str, Any]:
    if wire_mode == "soap":
        soap_action = {
            "ISSUE": "urn:pt-at:stub:2024:SubmitDocument",
            "CANCEL": "urn:pt-at:stub:2024:CancelDocument",
        }.get(operation, "urn:pt-at:stub:2024:Generic")
        canonical_bytes = json.dumps(canonical, separators=(",", ":"), default=str).encode("utf-8")
        b64 = base64.b64encode(canonical_bytes).decode("ascii")
        preview = (
            '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
            "<soap12:Body>"
            f'<at:FiscalRequest xmlns:at="https://stub.at.pt/f3b" soapAction="{soap_action}">'
            f"<at:PayloadB64>{b64[:12000]}</at:PayloadB64>"
            "</at:FiscalRequest>"
            "</soap12:Body></soap12:Envelope>"
        )
        return {
            "transport": "soap12",
            "soap_action": soap_action,
            "body_xml_preview": preview[:16000],
            "note": "Envelope sintético para testes (sem assinatura WS-Security).",
        }
    return {
        "transport": "http_json",
        "method": "POST",
        "path": f"/stub/at-pt/v1/{operation.lower()}",
        "body": canonical,
    }


def _build_issue_canonical(*, payload: dict[str, Any], access_key: str, invoice_number: str) -> dict[str, Any]:
    return {
        "contract_version": "f3b_at_pt_stub_gateway_v1",
        "provider_namespace": "at_pt_stub_gateway",
        "country": "PT",
        "operation": "ISSUE",
        "order_id": str(payload.get("order_id") or "").strip() or None,
        "invoice_id": str(payload.get("invoice_id") or "").strip() or None,
        "amount_cents": int(payload.get("amount_cents") or 0),
        "currency": str(payload.get("currency") or "EUR").strip().upper(),
        "access_key": access_key,
        "invoice_number": invoice_number,
        "invoice_series": "ATPT-GW-1",
    }


def _build_issue_provider_result(*, payload: dict[str, Any], access_key: str, invoice_number: str) -> dict[str, Any]:
    """Formato compatível com `normalize_issue_response` (country=PT)."""
    raw_inner = _build_issue_canonical(
        payload=payload, access_key=access_key, invoice_number=invoice_number
    )
    rec = f"at_pt_gw_rec_{uuid.uuid4().hex[:18]}"
    prot = f"at_pt_gw_prot_{uuid.uuid4().hex[:18]}"
    processed = _now_iso()
    return {
        "invoice_number": invoice_number,
        "invoice_series": "ATPT-GW-1",
        "access_key": access_key,
        "provider_status": "ACCEPTED",
        "provider_code": "AT-200",
        "provider_message": "Documento aceite pela AT (stub gateway F3B).",
        "receipt_number": rec,
        "protocol_number": prot,
        "government_response": {
            "provider_namespace": "at_pt_stub_gateway",
            "provider_status": "ACCEPTED",
            "provider_code": "AT-200",
            "provider_message": "Stub gateway — sem chamada à AT real.",
            "receipt_number": rec,
            "protocol_number": prot,
            "processed_at": processed,
            "raw": raw_inner,
        },
        "raw": raw_inner,
    }


def submit_at_pt_stub_issue(payload: dict[str, Any], *, wire_mode: str | None = None) -> dict[str, Any]:
    wire = _normalize_wire_mode(wire_mode or payload.get("wire_mode"))
    idempotency_key = _derive_idempotency_key(payload)

    with _LOCK:
        existing = _ISSUE_BY_IDEMPOTENCY.get(idempotency_key)
        if existing:
            return {
                "provider_namespace": "at_pt_stub_gateway",
                "operation": "ISSUE",
                "wire_mode": wire,
                "wire_envelope": existing["wire_envelope"],
                "idempotency_key": idempotency_key,
                "idempotent_replay": True,
                "provider_result": existing["provider_result"],
                "created_at": existing["created_at"],
            }

        inv_hint = str(payload.get("invoice_id") or "").strip() or uuid.uuid4().hex[:10].upper()
        invoice_number = f"ATPTGW{datetime.now(timezone.utc).strftime('%Y%m%d')}{inv_hint[-6:].upper()}"
        access_key = str(payload.get("access_key") or "").strip() or f"at_pt_gw_{uuid.uuid4().hex}"
        canonical = _build_issue_canonical(
            payload=payload, access_key=access_key, invoice_number=invoice_number
        )
        envelope = _wire_envelope(wire_mode=wire, operation="ISSUE", canonical=canonical)
        provider_result = _build_issue_provider_result(
            payload=payload, access_key=access_key, invoice_number=invoice_number
        )
        created_at = _now_iso()
        row = {
            "wire_envelope": envelope,
            "provider_result": provider_result,
            "created_at": created_at,
        }
        _ISSUE_BY_IDEMPOTENCY[idempotency_key] = row

    return {
        "provider_namespace": "at_pt_stub_gateway",
        "operation": "ISSUE",
        "wire_mode": wire,
        "wire_envelope": envelope,
        "idempotency_key": idempotency_key,
        "idempotent_replay": False,
        "provider_result": provider_result,
        "created_at": created_at,
    }


def submit_at_pt_stub_cancel(payload: dict[str, Any], *, wire_mode: str | None = None) -> dict[str, Any]:
    wire = _normalize_wire_mode(wire_mode or payload.get("wire_mode"))
    order_id = str(payload.get("order_id") or "").strip()
    invoice_id = str(payload.get("invoice_id") or "").strip()
    access_key_in = str(payload.get("access_key") or "").strip()
    if not order_id and not invoice_id and not access_key_in:
        raise ValueError("at_pt_stub_cancel_requires_access_key_or_order_or_invoice")
    access_key = access_key_in or f"at_pt_gw_{uuid.uuid4().hex}"

    canonical: dict[str, Any] = {
        "contract_version": "f3b_at_pt_stub_gateway_v1",
        "provider_namespace": "at_pt_stub_gateway",
        "country": "PT",
        "operation": "CANCEL",
        "order_id": order_id or None,
        "invoice_id": invoice_id or None,
        "access_key": access_key,
    }
    envelope = _wire_envelope(wire_mode=wire, operation="CANCEL", canonical=canonical)
    provider_result = {
        "provider": "at_pt",
        "country": "PT",
        "cancel_status": "CANCELLED",
        "access_key": access_key,
        "protocol_number": f"at_pt_gw_cancel_{uuid.uuid4().hex[:18]}",
        "processed_at": _now_iso(),
        "raw": canonical,
    }
    return {
        "provider_namespace": "at_pt_stub_gateway",
        "operation": "CANCEL",
        "wire_mode": wire,
        "wire_envelope": envelope,
        "provider_result": provider_result,
        "created_at": _now_iso(),
    }


def reset_at_pt_stub_gateway_state() -> dict[str, Any]:
    with _LOCK:
        n = len(_ISSUE_BY_IDEMPOTENCY)
        _ISSUE_BY_IDEMPOTENCY.clear()
    return {"ok": True, "cleared_idempotency_keys": n}
