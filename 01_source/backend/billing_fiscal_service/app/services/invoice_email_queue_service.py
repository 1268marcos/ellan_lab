# F-3 — Fila `invoice_email_outbox`: claim + envio SMTP opcional ou SENT_STUB.

from __future__ import annotations

import logging
import os
import smtplib
import socket
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice_email_outbox import InvoiceEmailOutbox
from app.services.invoice_delivery_service import record_invoice_delivery
from app.services.invoice_email_service import _redact_email

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    configured = os.getenv("INVOICE_ISSUE_WORKER_ID")
    if configured:
        return f"{configured}:email"
    return f"billing_fiscal_email:{socket.gethostname()}:{os.getpid()}"


def _lock_stale_before() -> datetime:
    return _utc_now() - timedelta(seconds=max(30, int(settings.invoice_email_lock_sec)))


def _backoff_sec(retry_count: int) -> int:
    base = max(15, int(settings.invoice_issue_base_backoff_sec))
    return min(3600, base * (2**max(0, retry_count - 1)))


def list_eligible_email_outbox_ids(db: Session, *, batch_size: int) -> list[str]:
    now = _utc_now()
    stale_before = _lock_stale_before()
    stmt = (
        select(InvoiceEmailOutbox.id)
        .where(InvoiceEmailOutbox.status == "PENDING")
        .where((InvoiceEmailOutbox.next_retry_at.is_(None)) | (InvoiceEmailOutbox.next_retry_at <= now))
        .where((InvoiceEmailOutbox.locked_at.is_(None)) | (InvoiceEmailOutbox.locked_at < stale_before))
        .order_by(InvoiceEmailOutbox.created_at.asc(), InvoiceEmailOutbox.id.asc())
        .limit(batch_size)
    )
    return list(db.execute(stmt).scalars().all())


def _claim_outbox_row(db: Session, *, outbox_id: str, worker_id: str) -> bool:
    now = _utc_now()
    stale_before = _lock_stale_before()
    stmt = (
        update(InvoiceEmailOutbox)
        .where(InvoiceEmailOutbox.id == outbox_id)
        .where(InvoiceEmailOutbox.status == "PENDING")
        .where((InvoiceEmailOutbox.next_retry_at.is_(None)) | (InvoiceEmailOutbox.next_retry_at <= now))
        .where((InvoiceEmailOutbox.locked_at.is_(None)) | (InvoiceEmailOutbox.locked_at < stale_before))
        .values(locked_by=worker_id, locked_at=now)
    )
    result = db.execute(stmt)
    return int(result.rowcount or 0) == 1


def claim_email_outbox(db: Session, *, outbox_id: str, worker_id: str | None = None) -> InvoiceEmailOutbox | None:
    wid = worker_id or _worker_id()
    if not _claim_outbox_row(db, outbox_id=outbox_id, worker_id=wid):
        db.rollback()
        return None
    db.commit()
    return db.query(InvoiceEmailOutbox).filter(InvoiceEmailOutbox.id == outbox_id).first()


def _send_smtp_plain(*, to_email: str, subject: str, body_text: str) -> None:
    host = (settings.smtp_host or "").strip()
    if not host:
        raise RuntimeError("INVOICE_SMTP_ENABLED exige SMTP_HOST")
    from_addr = (settings.smtp_from or settings.smtp_user or "noreply@localhost").strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body_text)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(host, int(settings.smtp_port)) as smtp:
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password or "")
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, int(settings.smtp_port)) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password or "")
            smtp.send_message(msg)


def process_claimed_email_outbox(db: Session, *, row: InvoiceEmailOutbox) -> InvoiceEmailOutbox:
    base_detail = {
        "outbox_id": row.id,
        "template": row.template,
        "invoice_id": row.invoice_id,
        "recipient": _redact_email(row.to_email),
    }
    merge = dict(row.detail_json or {})
    base_detail.update({k: v for k, v in merge.items() if k in ("order_id", "invoice_status")})

    use_smtp = bool(settings.invoice_smtp_enabled and (settings.smtp_host or "").strip())
    try:
        if use_smtp:
            _send_smtp_plain(to_email=row.to_email, subject=row.subject, body_text=row.body_text)
            row.status = "SENT"
            row.sent_at = _utc_now()
            row.last_error = None
            delivery_status = "SENT"
            note = "E-mail enviado via SMTP (F-3)."
        else:
            row.status = "SENT_STUB"
            row.sent_at = _utc_now()
            row.last_error = None
            delivery_status = "SENT_STUB"
            note = "Fila processada — INVOICE_SMTP_ENABLED=0 ou SMTP_HOST vazio; sem envio real."

        row.locked_by = None
        row.locked_at = None
        db.commit()
        db.refresh(row)
        record_invoice_delivery(
            db,
            invoice_id=row.invoice_id,
            channel="EMAIL_DANFE",
            status=delivery_status,
            detail={**base_detail, "note": note, "smtp": use_smtp},
        )
        db.commit()
        logger.info(
            "invoice_email_outbox_done",
            extra={"outbox_id": row.id, "invoice_id": row.invoice_id, "status": row.status},
        )
    except Exception as exc:
        err = str(exc)[:1900]
        row.retry_count = int(row.retry_count or 0) + 1
        row.last_error = err
        row.locked_by = None
        row.locked_at = None
        max_r = max(1, int(settings.invoice_email_max_retries))
        if row.retry_count >= max_r:
            row.status = "DEAD_LETTER"
            row.next_retry_at = None
            record_invoice_delivery(
                db,
                invoice_id=row.invoice_id,
                channel="EMAIL_DANFE",
                status="FAILED_EMAIL",
                detail={**base_detail, "note": "Máximo de tentativas na fila de e-mail.", "error": err},
            )
        else:
            row.status = "PENDING"
            row.next_retry_at = _utc_now() + timedelta(seconds=_backoff_sec(row.retry_count))
            record_invoice_delivery(
                db,
                invoice_id=row.invoice_id,
                channel="EMAIL_DANFE",
                status="RETRY_SCHEDULED",
                detail={
                    **base_detail,
                    "note": "Falha no envio; nova tentativa agendada.",
                    "error": err,
                    "retry_count": row.retry_count,
                },
            )
        db.commit()
        db.refresh(row)
        logger.warning(
            "invoice_email_outbox_failed",
            extra={"outbox_id": row.id, "invoice_id": row.invoice_id, "retry_count": row.retry_count, "error": err},
        )
    return row


def claim_and_process_email_outbox_by_id(
    db: Session,
    *,
    outbox_id: str,
    worker_id: str | None = None,
) -> InvoiceEmailOutbox | None:
    claimed = claim_email_outbox(db, outbox_id=outbox_id, worker_id=worker_id)
    if claimed is None:
        return None
    return process_claimed_email_outbox(db, row=claimed)
