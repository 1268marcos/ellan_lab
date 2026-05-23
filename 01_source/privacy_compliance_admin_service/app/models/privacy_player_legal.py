from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyPlayerLegalDocument(Base):
    """Documento legal de privacidade por player do ecossistema locker."""

    __tablename__ = "privacy_player_legal_documents"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(32), nullable=False, index=True)
    player_name = Column(String(128), nullable=False)
    document_slug = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    regulation_code = Column(String(16), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    language = Column(String(8), nullable=False, default="en")
    summary = Column(Text, nullable=True)
    public_path = Column(String(200), nullable=False)
    privacy_contact_email = Column(String(128), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    effective_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
