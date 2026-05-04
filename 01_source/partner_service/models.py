from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(String(36), primary_key=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")
    contact_email = Column(String(255), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret_hash = Column(String(128), nullable=True)
    webhook_events_json = Column(Text, nullable=False, default='["*"]')
    webhook_api_version = Column(String(10), nullable=False, default="v1")
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    api_keys = relationship("PartnerApiKey", back_populates="partner", cascade="all, delete-orphan")
    service_areas = relationship(
        "PartnerServiceArea", back_populates="partner", cascade="all, delete-orphan"
    )
    settlement_batches = relationship(
        "PartnerSettlementBatch", back_populates="partner", cascade="all, delete-orphan"
    )
    performance_metrics = relationship(
        "PartnerPerformanceMetric", back_populates="partner", cascade="all, delete-orphan"
    )


class PartnerApiKey(Base):
    __tablename__ = "partner_api_keys"

    __table_args__ = (Index("idx_pak_partner", "partner_id", "partner_type"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default="[]")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    partner = relationship("Partner", back_populates="api_keys")


class PartnerServiceArea(Base):
    __tablename__ = "partner_service_areas"

    __table_args__ = (Index("idx_psa_partner_priority", "partner_id", "priority", "created_at"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    locker_id = Column(String(36), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    exclusive = Column(Boolean, nullable=False, default=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    partner = relationship("Partner", back_populates="service_areas")


class PartnerSettlementBatch(Base):
    __tablename__ = "partner_settlement_batches"

    __table_args__ = (Index("idx_psb_partner_period", "partner_id", "period_start", "period_end"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    total_orders = Column(Integer, nullable=False, default=0)
    gross_revenue_cents = Column(BigInteger, nullable=False, default=0)
    revenue_share_pct = Column(Numeric(6, 4), nullable=False)
    revenue_share_cents = Column(BigInteger, nullable=False, default=0)
    fees_cents = Column(BigInteger, nullable=False, default=0)
    net_amount_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="DRAFT")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    settlement_ref = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    partner = relationship("Partner", back_populates="settlement_batches")
    items = relationship(
        "PartnerSettlementItem", back_populates="batch", cascade="all, delete-orphan"
    )


class PartnerSettlementItem(Base):
    __tablename__ = "partner_settlement_items"

    __table_args__ = (Index("idx_psi_batch", "batch_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), ForeignKey("partner_settlement_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    gross_cents = Column(BigInteger, nullable=False)
    share_pct = Column(Numeric(6, 4), nullable=False)
    share_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")

    batch = relationship("PartnerSettlementBatch", back_populates="items")


class PartnerPerformanceMetric(Base):
    __tablename__ = "partner_performance_metrics"

    __table_args__ = (Index("idx_ppm_partner_month", "partner_id", "period_month"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    period_month = Column(String(7), nullable=False)
    total_orders = Column(Integer, nullable=False, default=0)
    on_time_pickup_pct = Column(Numeric(5, 2), nullable=True)
    return_rate_pct = Column(Numeric(5, 2), nullable=True)
    avg_pickup_hours = Column(Numeric(6, 2), nullable=True)
    sla_compliance_pct = Column(Numeric(5, 2), nullable=True)
    webhook_success_rate = Column(Numeric(5, 2), nullable=True)
    generated_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    partner = relationship("Partner", back_populates="performance_metrics")
