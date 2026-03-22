# 01_source/backend/billing_fiscal_service/app/models/invoice_model.py
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    FAILED = "FAILED"


class Invoice(Base):
    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_invoice_order"),
        Index("ix_invoice_order_id", "order_id"),
        Index("ix_invoice_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    country: Mapped[str] = mapped_column(String(5), nullable=False, default="BR")
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False, default="NFE")

    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)

    xml_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)