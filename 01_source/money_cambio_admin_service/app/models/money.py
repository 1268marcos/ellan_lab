from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MoneyCurrencyCatalog(Base):
    __tablename__ = "money_currency_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    symbol = Column(String(8), nullable=True)
    minor_units = Column(Integer, nullable=False, default=2)
    numeric_code = Column(String(3), nullable=True)
    region_hint = Column(String(40), nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
