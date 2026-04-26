from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Index, Integer, String

from app.core.db import Base


class PartnerServiceArea(Base):
    __tablename__ = "partner_service_areas"

    __table_args__ = (
        Index("idx_psa_partner_priority", "partner_id", "priority", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    locker_id = Column(String(36), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    exclusive = Column(Boolean, nullable=False, default=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
