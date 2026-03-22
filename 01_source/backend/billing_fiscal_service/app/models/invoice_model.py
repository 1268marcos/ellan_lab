# 01_source/backend/billing_fiscal_service/app/models/invoice_model.py
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Enum, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ISSUED = "ISSUED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_invoice_order"),
        Index("ix_invoice_order_id", "order_id"),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_country_status", "country", "status"),
        Index("ix_invoice_created_at", "created_at"),
        Index("ix_invoice_next_retry_at", "next_retry_at"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    region: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(5), nullable=False, default="BR")
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False, default="NFE")

    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_series: Mapped[str | None] = mapped_column(String(50), nullable=True)
    access_key: Mapped[str | None] = mapped_column(String(120), nullable=True)

    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    amount_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoicestatus"),
        nullable=False,
        default=InvoiceStatus.PENDING,
    )

    xml_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tax_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    government_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    order_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)

    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )