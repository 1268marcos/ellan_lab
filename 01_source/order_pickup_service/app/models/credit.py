# 01_source/order_pickup_service/app/models/credit.py
# 21/04/2026 - crédito com validade temporal de 30 dias

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, String, Integer, Enum, DateTime, Text

from app.core.db import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreditStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class Credit(Base):
    __tablename__ = "credits"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    order_id = Column(String, nullable=False, unique=True)
    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(CreditStatus), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    source_type = Column(String(50), nullable=True)
    source_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def default_expires_at(*, now: datetime | None = None, days: int = 30) -> datetime:
        base = now or _utc_now()
        return base + timedelta(days=days)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def is_available_now(self, *, now: datetime | None = None) -> bool:
        ref = now or _utc_now()
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        exp = self.expires_at
        if exp is not None and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return (
            self.status == CreditStatus.AVAILABLE
            and exp is not None
            and exp > ref
            and self.used_at is None
            and self.revoked_at is None
        )
    
    