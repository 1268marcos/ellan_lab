from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LockerApiKey(Base):
    __tablename__ = "locker_api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    rotated_at = Column(DateTime, nullable=True)

    locker = relationship("Locker", back_populates="api_keys")
