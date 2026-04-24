from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FiscalReconciliationGap(Base):
    __tablename__ = "fiscal_reconciliation_gaps"

    __table_args__ = (
        Index("ix_fiscal_gap_status_last", "status", "last_detected_at"),
        Index("ix_fiscal_gap_order", "order_id"),
        Index("ix_fiscal_gap_invoice", "invoice_id"),
        Index("ix_fiscal_gap_type", "gap_type"),
    )

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    dedupe_key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    gap_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARN")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")

    order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
