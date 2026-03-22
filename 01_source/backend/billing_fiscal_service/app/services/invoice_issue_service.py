# 01_source/backend/billing_fiscal_service/app/services/invoice_issue_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_issue_invoice


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _compute_next_retry_at(retry_count: int) -> datetime:
    exponent = max(0, retry_count - 1)
    delay_sec = settings.invoice_issue_base_backoff_sec * (2 ** exponent)
    return _utc_now() + timedelta(seconds=delay_sec)


def mark_invoice_issued(db: Session, invoice: Invoice, fiscal_result: dict) -> Invoice:
    now = _utc_now()

    invoice.status = InvoiceStatus.ISSUED
    invoice.invoice_number = fiscal_result.get("invoice_number")
    invoice.invoice_series = fiscal_result.get("invoice_series")
    invoice.access_key = fiscal_result.get("access_key")
    invoice.tax_details = fiscal_result.get("tax_details")
    invoice.xml_content = fiscal_result.get("xml_content")
    invoice.government_response = fiscal_result.get("government_response")
    invoice.issued_at = now
    invoice.updated_at = now
    invoice.error_message = None
    invoice.last_error_code = None
    invoice.next_retry_at = None
    invoice.dead_lettered_at = None

    db.commit()
    db.refresh(invoice)
    return invoice


def mark_invoice_failed(db: Session, invoice: Invoice, error_message: str, error_code: str = "ISSUE_FAILED") -> Invoice:
    now = _utc_now()
    invoice.retry_count = int(invoice.retry_count or 0) + 1
    invoice.last_attempt_at = now
    invoice.updated_at = now
    invoice.error_message = (error_message or "")[:1000]
    invoice.last_error_code = error_code

    if invoice.retry_count >= settings.invoice_issue_max_retries:
        invoice.status = InvoiceStatus.DEAD_LETTER
        invoice.dead_lettered_at = now
        invoice.next_retry_at = None
    else:
        invoice.status = InvoiceStatus.FAILED
        invoice.next_retry_at = _compute_next_retry_at(invoice.retry_count)

    db.commit()
    db.refresh(invoice)
    return invoice


def issue_invoice(db: Session, invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.ISSUED:
        return invoice

    if invoice.status not in {
        InvoiceStatus.PENDING,
        InvoiceStatus.PROCESSING,
        InvoiceStatus.FAILED,
    }:
        raise ValueError(
            f"Invoice {invoice.id} em status inválido para emissão: {invoice.status}"
        )

    try:
        fiscal_result = route_issue_invoice(invoice)
    except Exception as exc:
        return mark_invoice_failed(db, invoice, str(exc), error_code="FISCAL_PROVIDER_EXCEPTION")

    result_status = str(fiscal_result.get("status") or "").upper()
    if result_status != "ISSUED":
        return mark_invoice_failed(
            db,
            invoice,
            f"Retorno fiscal inválido ou não emitido: {fiscal_result}",
            error_code="FISCAL_PROVIDER_INVALID_STATUS",
        )

    return mark_invoice_issued(db, invoice, fiscal_result)


def reset_invoice_for_retry(db: Session, invoice: Invoice, *, clear_identifiers: bool) -> Invoice:
    now = _utc_now()

    invoice.status = InvoiceStatus.PENDING
    invoice.next_retry_at = None
    invoice.dead_lettered_at = None
    invoice.error_message = None
    invoice.last_error_code = None
    invoice.processing_started_at = None
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.updated_at = now

    if clear_identifiers:
        invoice.invoice_number = None
        invoice.invoice_series = None
        invoice.access_key = None
        invoice.tax_details = None
        invoice.xml_content = None
        invoice.government_response = None
        invoice.issued_at = None

    db.commit()
    db.refresh(invoice)
    return invoice