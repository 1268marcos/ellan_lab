from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_role = Column(String(40), nullable=True)
    action = Column(String(80), nullable=False)
    target_type = Column(String(40), nullable=False)
    target_id = Column(String(36), nullable=False)
    old_state = Column(JsonType, nullable=True)
    new_state = Column(JsonType, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    source_service = Column(String(64), nullable=True)
    immutable = Column(Boolean, nullable=False, default=True)
