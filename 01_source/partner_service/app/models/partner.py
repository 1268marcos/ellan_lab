from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(64), nullable=False, default="ECOMMERCE")
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    api_keys: Mapped[list[PartnerApiKey]] = relationship(back_populates="partner", cascade="all, delete-orphan")
    service_areas: Mapped[list[PartnerServiceArea]] = relationship(
        back_populates="partner", cascade="all, delete-orphan"
    )
    settlement_batches: Mapped[list[PartnerSettlementBatch]] = relationship(
        back_populates="partner", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[list[PartnerPerformanceMetric]] = relationship(
        back_populates="partner", cascade="all, delete-orphan"
    )
    webhook_subscriptions: Mapped[list] = relationship(
        "PartnerWebhookSubscription", back_populates="partner", cascade="all, delete-orphan"
    )


class PartnerApiKey(Base):
    __tablename__ = "partner_api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(64), ForeignKey("partners.id"), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    partner: Mapped[Partner] = relationship(back_populates="api_keys")


class PartnerServiceArea(Base):
    __tablename__ = "partner_service_areas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(64), ForeignKey("partners.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    geojson: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped[Partner] = relationship(back_populates="service_areas")


class PartnerSettlementBatch(Base):
    __tablename__ = "partner_settlement_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(64), ForeignKey("partners.id"), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    partner: Mapped[Partner] = relationship(back_populates="settlement_batches")


class PartnerPerformanceMetric(Base):
    __tablename__ = "partner_performance_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(64), ForeignKey("partners.id"), nullable=False, index=True)
    metric_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deliveries_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deliveries_fail: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    partner: Mapped[Partner] = relationship(back_populates="performance_metrics")
