# I-2 — Endpoints fiscais auxiliares (DANFE térmico stub).

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.fiscal_authority_callback import FiscalAuthorityCallback
from app.models.invoice_model import Invoice

router = APIRouter(prefix="/internal/fiscal", tags=["fiscal"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


@router.get("/danfe/{invoice_id}/thermal")
def get_danfe_thermal_json(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    JSON para impressora térmica (stub). Substituir por layout ESC/POS real em F-3.
    """
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    snap = inv.order_snapshot or {}
    order = snap.get("order") or {}
    return {
        "format": "thermal_json_v1",
        "width_mm": 80,
        "invoice_id": inv.id,
        "order_id": inv.order_id,
        "access_key": inv.access_key,
        "invoice_number": inv.invoice_number,
        "invoice_series": inv.invoice_series,
        "status": str(getattr(inv.status, "value", inv.status)),
        "lines": [
            {"text": "DANFE NFC-e (stub)", "style": "header"},
            {"text": f"Pedido: {inv.order_id}", "style": "body"},
            {"text": f"SKU: {order.get('sku_id', '')}", "style": "body"},
            {"text": f"Chave: {inv.access_key or '—'}", "style": "small"},
        ],
    }


@router.post("/callback")
def receive_authority_callback(
    payload: dict,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    F-3: callback assíncrono de autoridade fiscal (SEFAZ/AT/AEAT).
    Persiste payload bruto e anexa histórico em government_response da invoice.
    """
    invoice_id = str(payload.get("invoice_id") or "").strip()
    authority = str(payload.get("authority") or "").strip().upper()
    if not invoice_id:
        raise HTTPException(status_code=400, detail="invoice_id is required")
    if authority not in {"SEFAZ", "AT", "AEAT"}:
        raise HTTPException(status_code=400, detail="authority must be one of: SEFAZ, AT, AEAT")

    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    now = datetime.now(timezone.utc)
    row = FiscalAuthorityCallback(
        id=f"fac_{uuid.uuid4().hex[:24]}",
        invoice_id=invoice_id,
        authority=authority,
        event_type=str(payload.get("event_type") or "").strip() or None,
        status=str(payload.get("status") or "").strip() or None,
        protocol_number=str(payload.get("protocol_number") or "").strip() or None,
        raw_payload=payload,
        received_at=now,
    )
    db.add(row)

    gr = dict(inv.government_response or {})
    callbacks = list(gr.get("authority_callbacks") or [])
    callbacks.append(
        {
            "callback_id": row.id,
            "authority": row.authority,
            "event_type": row.event_type,
            "status": row.status,
            "protocol_number": row.protocol_number,
            "received_at": now.isoformat(),
        }
    )
    gr["authority_callbacks"] = callbacks
    inv.government_response = gr
    db.commit()
    db.refresh(row)

    return {
        "ok": True,
        "callback_id": row.id,
        "invoice_id": row.invoice_id,
        "authority": row.authority,
    }
