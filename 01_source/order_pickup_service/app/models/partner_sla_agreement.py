from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Index, Integer, Numeric, String

from app.core.db import Base


class PartnerSlaAgreement(Base):
    __tablename__ = "partner_sla_agreements"

    __table_args__ = (
        Index("idx_psa_partner_active", "partner_id", "is_active"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False, default="BR")
    product_category = Column(String(64), nullable=True)
    sla_pickup_hours = Column(Integer, nullable=False, default=72)
    sla_return_hours = Column(Integer, nullable=False, default=24)
    penalty_pct = Column(Numeric(5, 2), nullable=False, default=0)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
