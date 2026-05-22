from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SellerApiKey(Base):
    __tablename__ = "seller_api_keys"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default="[]")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
