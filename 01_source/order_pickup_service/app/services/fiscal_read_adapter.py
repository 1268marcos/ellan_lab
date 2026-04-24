"""
Adapta resposta do billing_fiscal_service para o formato esperado por
`/public/fiscal/*` e serializadores que antes liam apenas `FiscalDocument`.
"""

from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _coerce_dict(val: Any) -> dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            out = json.loads(val)
            return out if isinstance(out, dict) else {}
        except Exception:
            return {}
    return {}


@dataclass
class FiscalReadView:
    """
    Visão somente leitura alinhada aos campos usados por public_fiscal e
    _serialize_order* (receipt_code, print_site_path, payload_json, …).
    """

    id: str
    order_id: str
    receipt_code: str
    document_type: str
    channel: str | None
    region: str | None
    amount_cents: int
    currency: str
    delivery_mode: str | None
    send_status: str | None
    send_target: str | None
    print_status: str | None
    print_site_path: str | None
    payload_json: dict[str, Any]
    issued_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    attempt: int = 1
    source: str = "billing"


def fiscal_read_view_from_billing_invoice(inv: dict[str, Any]) -> FiscalReadView:
    snap = _coerce_dict(inv.get("order_snapshot"))
    order = _coerce_dict(snap.get("order"))
    allocation = _coerce_dict(snap.get("allocation"))
    pickup = _coerce_dict(snap.get("pickup"))
    gov = _coerce_dict(inv.get("government_response"))

    def _short_mode_tag(emission_mode: str | None) -> str:
        mode = str(emission_mode or "").strip().upper()
        if mode == "ONLINE":
            return "ONL"
        if mode == "OFFLINE_SAT":
            return "SAT"
        if mode == "CONTINGENCY_SVRS":
            return "CSV"
        return (mode[:3] or "UNK").ljust(3, "X")

    access_key = str(inv.get("access_key") or "").strip()
    short_receipt = None
    if access_key:
        seed = access_key or str(inv.get("id") or "")
        digest8 = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8].upper()
        short_receipt = f"{str(inv.get('country') or 'BR').upper()[:2]}-{_short_mode_tag(inv.get('emission_mode'))}-{digest8}"

    receipt = (
        short_receipt
        or inv.get("access_key")
        or inv.get("invoice_number")
        or gov.get("receipt_number")
    )
    if not receipt:
        oid = str(inv.get("order_id") or "")
        receipt = f"BILL-{oid[:12].upper()}" if oid else "BILL-UNKNOWN"

    inv_payload = _coerce_dict(inv.get("payload_json"))
    payload: dict[str, Any] = {
        "order": order,
        "allocation": allocation,
        "pickup": pickup,
        "mode": "BILLING",
        "print_label": "Documento fiscal (billing)",
        "receipt_code": receipt,
        "receipt_code_full": access_key or None,
        "invoice_id": inv.get("id"),
        "invoice_status": inv.get("status"),
        "manual_generated_without_domain_event": bool(inv_payload.get("manual_generated_without_domain_event")),
        "receipt_lookup_supported": True,
    }

    amount = inv.get("amount_cents")
    try:
        amount_cents = int(amount) if amount is not None else int(order.get("amount_cents") or 0)
    except Exception:
        amount_cents = 0

    currency = str(inv.get("currency") or order.get("currency") or "BRL")
    st = str(inv.get("status") or "").upper()

    issued_at = _parse_dt(inv.get("issued_at")) or _parse_dt(inv.get("created_at"))
    created_at = _parse_dt(inv.get("created_at")) or issued_at
    updated_at = _parse_dt(inv.get("updated_at")) or created_at

    return FiscalReadView(
        id=str(inv.get("id") or receipt),
        order_id=str(inv.get("order_id") or ""),
        receipt_code=str(receipt),
        document_type=str(inv.get("invoice_type") or "INVOICE"),
        channel=order.get("channel"),
        region=order.get("region") or inv.get("region"),
        amount_cents=amount_cents,
        currency=currency,
        delivery_mode="BOTH",
        send_status=st or None,
        send_target=None,
        print_status="READY" if st == "ISSUED" else "PENDING",
        print_site_path=None,
        payload_json=payload,
        issued_at=issued_at or datetime.now(timezone.utc),
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=updated_at or datetime.now(timezone.utc),
        attempt=1,
        source="billing",
    )


def extract_attempt_from_fiscal_payload(fiscal_payload: dict | str | None) -> int:
    if not fiscal_payload:
        return 1
    if isinstance(fiscal_payload, str):
        try:
            fiscal_payload = json.loads(fiscal_payload)
        except Exception:
            fiscal_payload = {}
    if not isinstance(fiscal_payload, dict):
        return 1
    receipt_code = str(fiscal_payload.get("receipt_code", "") or "")
    match = re.search(r"-ATT(\d{2})", receipt_code)
    if match:
        return int(match.group(1))
    return 1
