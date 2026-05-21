from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LockerWebhookConfig(Base):
    __tablename__ = "locker_webhook_configs"

    locker_id = Column(String(64), ForeignKey("lockers.id"), primary_key=True)
    url = Column(String(512), nullable=False)
    secret_hash = Column(String(128), nullable=True)
    events = Column(Text, nullable=False, default="locker.created,locker.updated")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    locker = relationship("Locker", back_populates="webhook")
