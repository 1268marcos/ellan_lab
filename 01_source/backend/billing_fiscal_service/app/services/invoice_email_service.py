# I-2 / F-3 — E-mail DANFE: fila `invoice_email_outbox` + worker (SMTP opcional).

from __future__ import annotations

import hashlib
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.invoice_email_outbox import InvoiceEmailOutbox
from app.models.invoice_model import Invoice
from app.services.invoice_delivery_service import record_invoice_delivery

logger = logging.getLogger(__name__)


def extract_receipt_email(invoice: Invoice) -> str | None:
    snap = invoice.order_snapshot or {}
    order = snap.get("order") or {}
    if not isinstance(order, dict):
        return None
    for key in ("receipt_email", "guest_email"):
        raw = order.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if s and "@" in s:
            return s
    return None


def _redact_email(email: str) -> dict:
    """Metadados seguros para log (sem armazenar e-mail completo)."""
    parts = email.rsplit("@", 1)
    if len(parts) != 2:
        return {"to_hash": hashlib.sha256(email.encode()).hexdigest()[:16]}
    local, domain = parts[0], parts[1]
    tip = (local[:2] + "***") if len(local) > 2 else "***"
    return {"to_preview": f"{tip}@{domain}", "to_hash": hashlib.sha256(email.encode()).hexdigest()[:16]}


def build_danfe_email_content(
    *,
    invoice: Invoice,
    template: str,
    extra_detail: dict | None = None,
) -> tuple[str, str]:
    """Assunto e corpo texto plano para templates issued | cancelled | cce_applied."""
    ref = invoice.access_key or invoice.invoice_number or invoice.id
    order_id = invoice.order_id
    extra = extra_detail or {}
    if template == "issued":
        subject = f"Nota fiscal — pedido {order_id}"
        body = (
            f"Sua nota fiscal foi emitida.\n\n"
            f"Pedido: {order_id}\n"
            f"Referência: {ref}\n"
            f"Documento: {invoice.invoice_type} ({invoice.country})\n\n"
            f"Em anexo ou link DANFE (quando integração estiver completa).\n"
        )
    elif template == "cancelled":
        subject = f"Cancelamento de nota — pedido {order_id}"
        body = (
            f"O documento fiscal do pedido {order_id} foi cancelado.\n\n"
            f"Referência: {ref}\n"
            f"Estado: {extra.get('invoice_status', 'CANCELLED')}\n"
        )
    elif template == "cce_applied":
        subject = f"Carta de correção — pedido {order_id}"
        body = (
            f"Foi registrada uma carta de correção (CC-e) para o pedido {order_id}.\n\n"
            f"Referência: {ref}\n"
        )
    else:
        subject = f"Notificação fiscal — pedido {order_id}"
        body = f"Atualização fiscal.\n\nPedido: {order_id}\nReferência: {ref}\n"
    return subject, body


def send_danfe_email_stub(
    db: Session,
    *,
    invoice: Invoice,
    template: str,
    extra_detail: dict | None = None,
) -> None:
    """
    Enfileira envio em `invoice_email_outbox` (F-3). O worker grava SENT ou SENT_STUB em `invoice_delivery_log`.
    `template`: issued | cancelled | cce_applied
    """
    to = extract_receipt_email(invoice)
    base = {
        "template": template,
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
    }
    if extra_detail:
        base.update(extra_detail)

    if not to:
        record_invoice_delivery(
            db,
            invoice_id=invoice.id,
            channel="EMAIL_DANFE",
            status="SKIPPED_NO_RECIPIENT",
            detail={**base, "note": "order_snapshot sem receipt_email/guest_email válido"},
        )
        logger.info("invoice_email_stub_skipped_no_recipient", extra={"invoice_id": invoice.id})
        return

    subject, body_text = build_danfe_email_content(
        invoice=invoice, template=template, extra_detail=extra_detail
    )
    outbox_id = f"iem_{uuid.uuid4().hex[:22]}"
    detail_json = {**base, "recipient_redacted": _redact_email(to)}
    row = InvoiceEmailOutbox(
        id=outbox_id,
        invoice_id=invoice.id,
        template=template,
        to_email=to,
        subject=subject,
        body_text=body_text,
        detail_json=detail_json,
        status="PENDING",
    )
    db.add(row)
    detail = {**base, "recipient": _redact_email(to), "outbox_id": outbox_id}
    record_invoice_delivery(
        db,
        invoice_id=invoice.id,
        channel="EMAIL_DANFE",
        status="QUEUED",
        detail={**detail, "note": "Enfileirado em invoice_email_outbox (F-3)."},
    )
    logger.info(
        "invoice_email_enqueued",
        extra={"invoice_id": invoice.id, "template": template, "outbox_id": outbox_id},
    )


def send_danfe_email_after_issue(invoice_id: str) -> None:
    """Chamada pós-commit da emissão (sessão própria para não afetar invoice)."""
    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not inv:
            return
        send_danfe_email_stub(db, invoice=inv, template="issued")
        db.commit()
    except Exception:
        logger.exception("invoice_email_after_issue_failed", extra={"invoice_id": invoice_id})
        db.rollback()
    finally:
        db.close()


def send_danfe_email_after_cancel(invoice_id: str) -> None:
    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not inv:
            return
        send_danfe_email_stub(db, invoice=inv, template="cancelled", extra_detail={"invoice_status": "CANCELLED"})
        db.commit()
    except Exception:
        logger.exception("invoice_email_after_cancel_failed", extra={"invoice_id": invoice_id})
        db.rollback()
    finally:
        db.close()


def send_danfe_email_after_cce(invoice_id: str) -> None:
    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not inv:
            return
        send_danfe_email_stub(db, invoice=inv, template="cce_applied", extra_detail={"cce_stub": True})
        db.commit()
    except Exception:
        logger.exception("invoice_email_after_cce_failed", extra={"invoice_id": invoice_id})
        db.rollback()
    finally:
        db.close()
