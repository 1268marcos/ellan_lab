from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, Date, DateTime, Index, Integer, Numeric, String, Text

from app.core.db import Base


class PartnerSettlementBatch(Base):
    __tablename__ = "partner_settlement_batches"

    __table_args__ = (
        Index("idx_psb_partner_period", "partner_id", "period_start", "period_end"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
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
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class PartnerSettlementItem(Base):
    __tablename__ = "partner_settlement_items"

    __table_args__ = (
        Index("idx_psi_batch", "batch_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    gross_cents = Column(BigInteger, nullable=False)
    share_pct = Column(Numeric(6, 4), nullable=False)
    share_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
