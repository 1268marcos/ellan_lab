# I-2 — Endpoints fiscais auxiliares (DANFE térmico stub).

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
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
