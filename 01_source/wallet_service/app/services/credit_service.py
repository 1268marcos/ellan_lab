from __future__ import annotations

from datetime import datetime

from redis import Redis
from sqlalchemy.orm import Session

from app.models.credit import Credit
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.services import wallet_service


def create_promotional_credit(
    db: Session, r: Redis | None, user_id: str, amount: int, promotional: bool, expires_at: datetime | None
) -> Credit:
    wallet_service.get_or_create_wallet(db, user_id)
    c = Credit(user_id=user_id, amount=amount, remaining=amount, promotional=promotional, expires_at=expires_at)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def apply_credit(db: Session, r: Redis | None, user_id: str, credit_id: str, transaction_id: str) -> tuple[Credit, Wallet, Transaction]:
    c = db.get(Credit, credit_id)
    if not c or c.user_id != user_id:
        raise ValueError("credit_not_found")
    if c.remaining <= 0:
        raise ValueError("credit_empty")
    amt = c.remaining
    c.remaining = 0
    db.commit()
    w, t = wallet_service.credit_wallet(db, r, user_id, amt, transaction_id, tx_type="apply_credit")
    return c, w, t


def expire_pickup_debit(db: Session, r: Redis | None, user_id: str, amount: int, transaction_id: str) -> tuple[Wallet, Transaction]:
    return wallet_service.debit_wallet(db, r, user_id, amount, transaction_id)
