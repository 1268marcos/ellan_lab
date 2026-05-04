from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerWebhookSubscription(Base):
    __tablename__ = "partner_webhook_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(36), ForeignKey("partners.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    events: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    partner = relationship("Partner", back_populates="webhook_subscriptions")
    deliveries: Mapped[list[PartnerWebhookDelivery]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )


class PartnerWebhookDelivery(Base):
    __tablename__ = "partner_webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("partner_webhook_subscriptions.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    subscription: Mapped[PartnerWebhookSubscription] = relationship(back_populates="deliveries")
