from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base
from app.models.professional import JsonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MoneyPlayerPaymentRail(Base):
    __tablename__ = "money_player_payment_rail"
    __table_args__ = (
        UniqueConstraint(
            "player_code",
            "country_code",
            "payment_method_code",
            "wallet_provider_code",
            "channel",
            name="uq_mppr_player_rail",
        ),
    )

    id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    payment_method_code = Column(String(80), nullable=True)
    wallet_provider_code = Column(String(80), nullable=True)
    channel = Column(String(16), nullable=False, default="LOCKER")
    is_enabled = Column(Boolean, nullable=False, default=True)
    max_amount_cents = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyFxLock(Base):
    __tablename__ = "money_fx_lock"

    id = Column(String(36), primary_key=True)
    lock_reference = Column(String(48), nullable=False, unique=True, index=True)
    player_code = Column(String(48), nullable=True, index=True)
    corridor_code = Column(String(48), nullable=False, index=True)
    base_currency = Column(String(8), nullable=False)
    quote_currency = Column(String(8), nullable=False)
    locked_rate = Column(Numeric(18, 8), nullable=False)
    spread_bps = Column(Integer, nullable=False, default=0)
    amount_cents_ref = Column(BigInteger, nullable=True)
    status = Column(String(16), nullable=False, default="ACTIVE")
    locked_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class MoneyOpsQuoteLog(Base):
    __tablename__ = "money_ops_quote_log"

    id = Column(String(36), primary_key=True)
    quote_type = Column(String(32), nullable=False, index=True)
    player_code = Column(String(48), nullable=True)
    corridor_code = Column(String(48), nullable=True)
    request_json = Column(JsonType, nullable=False, default=dict)
    result_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
