from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_transactions_txid"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("wallets.user_id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    tx_type: Mapped[str] = mapped_column("tx_type", String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc)
