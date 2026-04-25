from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class OrderFulfillmentTracking(Base):
    __tablename__ = "order_fulfillment_tracking"

    __table_args__ = (
        Index("idx_oft_status_updated", "status", "updated_at"),
        Index("idx_oft_partner_status", "partner_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    fulfillment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ECOMMERCE_PARTNER")
    partner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    last_event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_outbox_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    allocated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispensed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
