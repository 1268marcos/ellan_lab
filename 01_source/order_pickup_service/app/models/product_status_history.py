from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text

from app.core.db import Base


class ProductStatusHistory(Base):
    __tablename__ = "product_status_history"

    __table_args__ = (
        Index("idx_prsh_product", "product_id", "changed_at"),
    )

    id = Column(String(36), primary_key=True)
    product_id = Column(String(255), nullable=False, index=True)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    reason = Column(Text, nullable=True)
    changed_by = Column(String(36), nullable=True)
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
