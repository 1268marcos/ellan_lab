# I-2 — Log de entrega de documento (e-mail DANFE, etc.).

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvoiceDeliveryLog(Base):
    __tablename__ = "invoice_delivery_log"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(50), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
