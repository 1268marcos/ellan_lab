from __future__ import annotations

import json
from datetime import datetime, timezone

from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.transaction import Transaction
from app.models.wallet import Wallet


class OptimisticLockError(Exception):
    pass


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_wallet(db: Session, user_id: str) -> Wallet:
    w = db.get(Wallet, user_id)
    if w:
        return w
    w = Wallet(user_id=user_id, balance=0, version=1)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def cache_balance_key(user_id: str) -> str:
    return f"wallet:balance:{user_id}"


def get_cached_balance(r: Redis | None, user_id: str) -> int | None:
    if r is None:
        return None
    settings = get_settings()
    raw = r.get(cache_balance_key(user_id))
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    return int(raw)


def set_cached_balance(r: Redis | None, user_id: str, balance: int) -> None:
    if r is None:
        return
    settings = get_settings()
    r.setex(cache_balance_key(user_id), settings.balance_cache_ttl, str(balance))


def mirror_event(r: Redis | None, event_type: str, payload: dict) -> None:
    if r is None:
        return
    settings = get_settings()
    body = json.dumps({"type": event_type, "payload": payload})
    r.xadd(settings.wallet_events_stream, {"data": body})


def credit_wallet(
    db: Session,
    r: Redis | None,
    user_id: str,
    amount: int,
    transaction_id: str,
    tx_type: str = "credit",
) -> tuple[Wallet, Transaction]:
    existing = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
    if existing:
        w = db.get(Wallet, existing.user_id)
        if not w:
            raise ValueError("wallet_missing")
        return w, existing

    w = get_or_create_wallet(db, user_id)
    w.balance += amount
    w.version += 1
    w.updated_at = _utc()
    t = Transaction(user_id=user_id, amount=amount, tx_type=tx_type, status="completed", transaction_id=transaction_id)
    db.add(t)
    db.commit()
    db.refresh(w)
    db.refresh(t)
    set_cached_balance(r, user_id, w.balance)
    mirror_event(r, "wallet.credited", {"user_id": user_id, "amount": amount, "transaction_id": transaction_id})
    return w, t


def debit_wallet(db: Session, r: Redis | None, user_id: str, amount: int, transaction_id: str, expected_version: int | None = None) -> tuple[Wallet, Transaction]:
    existing = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
    if existing:
        w = db.get(Wallet, existing.user_id)
        if not w:
            raise ValueError("wallet_missing")
        return w, existing

    w = get_or_create_wallet(db, user_id)
    if expected_version is not None and w.version != expected_version:
        raise OptimisticLockError("version_mismatch")
    if w.balance < amount:
        mirror_event(r, "wallet.insufficient_funds", {"user_id": user_id, "amount": amount, "transaction_id": transaction_id})
        raise ValueError("insufficient_funds")
    w.balance -= amount
    w.version += 1
    w.updated_at = _utc()
    t = Transaction(user_id=user_id, amount=-amount, tx_type="debit", status="completed", transaction_id=transaction_id)
    db.add(t)
    db.commit()
    db.refresh(w)
    db.refresh(t)
    set_cached_balance(r, user_id, w.balance)
    mirror_event(r, "wallet.debited", {"user_id": user_id, "amount": amount, "transaction_id": transaction_id})
    return w, t


def ledger_sum(db: Session, user_id: str) -> int:
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user_id)).all()
    return int(sum(t.amount for t in rows))
