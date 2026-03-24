# 01_source/backend/billing_fiscal_service/app/models/processed_event.py
# Existe em / candidato a legado / criado em local errado????
# 01_source/backend/order_lifecycle/app/models/processed_event.py
# 
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utc_now():
    return datetime.now(timezone.utc)


class ProcessedEvent(Base):
    __tablename__ = "billing_processed_events"

    __table_args__ = (
        UniqueConstraint("event_key", name="uq_billing_processed_event_key"),
        Index("ix_billing_processed_events_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    event_key: Mapped[str] = mapped_column(String(200), nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False)  
    # PROCESSED | FAILED | DEAD

    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )