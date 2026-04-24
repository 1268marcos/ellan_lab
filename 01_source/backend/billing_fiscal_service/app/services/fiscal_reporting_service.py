from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice_email_outbox import InvoiceEmailOutbox
from app.models.invoice_model import Invoice, InvoiceStatus


def month_bounds_utc(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


def get_issued_invoices_for_period(
    db: Session, *, year: int, month: int, country: str | None = None
) -> list[Invoice]:
    start, end = month_bounds_utc(year, month)
    q = db.query(Invoice).filter(Invoice.issued_at.isnot(None))
    q = q.filter(Invoice.issued_at >= start).filter(Invoice.issued_at < end)
    q = q.filter(Invoice.status == InvoiceStatus.ISSUED)
    if country:
        q = q.filter(Invoice.country == country.upper())
    return q.order_by(Invoice.issued_at.asc()).all()


def build_sped_efd_export_payload(*, year: int, month: int, invoices: list[Invoice]) -> dict:
    total_amount_cents = sum(int(inv.amount_cents or 0) for inv in invoices)
    return {
        "format": "SPED_EFD_STUB_V1",
        "year": year,
        "month": month,
        "invoice_count": len(invoices),
        "total_amount_cents": total_amount_cents,
        "records": [
            {
                "invoice_id": inv.id,
                "order_id": inv.order_id,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "access_key": inv.access_key,
                "amount_cents": int(inv.amount_cents or 0),
                "tax_breakdown_json": inv.tax_breakdown_json,
            }
            for inv in invoices
        ],
    }


def build_saft_pt_export_payload(*, year: int, month: int, invoices: list[Invoice]) -> dict:
    total_amount_cents = sum(int(inv.amount_cents or 0) for inv in invoices)
    return {
        "format": "SAFT_PT_STUB_V1",
        "year": year,
        "month": month,
        "invoice_count": len(invoices),
        "currency": "EUR",
        "total_amount_cents": total_amount_cents,
        "sales_invoices": [
            {
                "invoice_no": inv.invoice_number or inv.id,
                "invoice_id": inv.id,
                "order_id": inv.order_id,
                "issue_date": inv.issued_at.date().isoformat() if inv.issued_at else None,
                "hash_stub": inv.access_key,
                "gross_total_cents": int(inv.amount_cents or 0),
            }
            for inv in invoices
        ],
    }


def collect_dead_letter_summary(db: Session, *, threshold: int = 10) -> dict:
    inv_dead = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == InvoiceStatus.DEAD_LETTER)
        .scalar()
    ) or 0
    email_dead = (
        db.query(func.count(InvoiceEmailOutbox.id))
        .filter(InvoiceEmailOutbox.status == "DEAD_LETTER")
        .scalar()
    ) or 0
    total = int(inv_dead) + int(email_dead)
    return {
        "invoice_dead_letters": int(inv_dead),
        "email_dead_letters": int(email_dead),
        "total_dead_letters": total,
        "alert_threshold": int(threshold),
        "alert": total >= int(threshold),
    }
