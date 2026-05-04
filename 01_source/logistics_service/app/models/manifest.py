from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc() -> datetime:
    return datetime.now(timezone.utc)


class Manifest(Base):
    __tablename__ = "manifests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipments: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    locker_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc)
    deliveries: Mapped[list["Delivery"]] = relationship("Delivery", back_populates="manifest")
