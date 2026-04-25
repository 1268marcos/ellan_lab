from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, String

from app.core.db import Base


class PartnerContact(Base):
    __tablename__ = "partner_contacts"

    __table_args__ = (
        Index("idx_pc_partner", "partner_id", "contact_type"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    contact_type = Column(String(20), nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
