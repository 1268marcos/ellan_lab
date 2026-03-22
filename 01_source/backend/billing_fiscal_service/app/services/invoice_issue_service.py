# 01_source/backend/billing_fiscal_service/app/services/invoice_issue_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_issue_invoice


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def mark_invoice_processing(db: Session, invoice: Invoice) -> Invoice:
    invoice.status = InvoiceStatus.PROCESSING
    invoice.processing_started_at = _utc_now()
    invoice.updated_at = _utc_now()
    invoice.error_message = None
    db.commit()
    db.refresh(invoice)
    return invoice


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

    db.commit()
    db.refresh(invoice)
    return invoice


def mark_invoice_failed(db: Session, invoice: Invoice, error_message: str) -> Invoice:
    invoice.status = InvoiceStatus.FAILED
    invoice.error_message = (error_message or "")[:1000]
    invoice.updated_at = _utc_now()
    db.commit()
    db.refresh(invoice)
    return invoice


def issue_invoice(db: Session, invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.ISSUED:
        return invoice

    if invoice.status not in {InvoiceStatus.PENDING, InvoiceStatus.FAILED}:
        raise ValueError(
            f"Invoice {invoice.id} em status inválido para emissão: {invoice.status}"
        )

    mark_invoice_processing(db, invoice)

    try:
        fiscal_result = route_issue_invoice(invoice)
    except Exception as exc:
        return mark_invoice_failed(db, invoice, str(exc))

    result_status = str(fiscal_result.get("status") or "").upper()
    if result_status != "ISSUED":
        return mark_invoice_failed(
            db,
            invoice,
            f"Retorno fiscal inválido ou não emitido: {fiscal_result}",
        )

    return mark_invoice_issued(db, invoice, fiscal_result)
