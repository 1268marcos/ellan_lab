from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text

from app.core.db import Base


class PartnerStatusHistory(Base):
    __tablename__ = "partner_status_history"

    __table_args__ = (
        Index("idx_psh_partner", "partner_id", "changed_at"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    reason = Column(Text, nullable=True)
    changed_by = Column(String(36), nullable=True)
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
