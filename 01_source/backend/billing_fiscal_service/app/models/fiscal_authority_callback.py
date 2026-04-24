from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FiscalAuthorityCallback(Base):
    __tablename__ = "fiscal_authority_callbacks"

    __table_args__ = (
        Index("ix_fiscal_cb_invoice", "invoice_id"),
        Index("ix_fiscal_cb_authority", "authority"),
        Index("ix_fiscal_cb_received_at", "received_at"),
    )

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    authority: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    protocol_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
