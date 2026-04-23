# I-2 — Registro de entregas (e-mail DANFE, CC-e, etc.).

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.invoice_delivery_log import InvoiceDeliveryLog


def record_invoice_delivery(
    db: Session,
    *,
    invoice_id: str,
    channel: str,
    status: str,
    detail: dict | None = None,
) -> InvoiceDeliveryLog:
    row = InvoiceDeliveryLog(
        id=f"idl_{uuid.uuid4().hex[:24]}",
        invoice_id=invoice_id,
        channel=channel,
        status=status,
        detail=detail or {},
    )
    db.add(row)
    return row
