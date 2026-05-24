from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.advanced import MoneyFxLock
from app.models.professional import CambioPaymentCorridor
from app.schemas.advanced import FxLockIn
from app.services import fx_service
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _expire_stale(db: Session) -> None:
    now = _utcnow()
    db.query(MoneyFxLock).filter(
        MoneyFxLock.status == "ACTIVE",
        MoneyFxLock.expires_at < now,
    ).update({"status": "EXPIRED"})


def list_locks(db: Session, *, status: str | None = "ACTIVE") -> list[MoneyFxLock]:
    _expire_stale(db)
    q = db.query(MoneyFxLock)
    if status:
        q = q.filter(MoneyFxLock.status == status.upper())
    return q.order_by(MoneyFxLock.expires_at.desc()).limit(100).all()


def create_lock(db: Session, body: FxLockIn) -> MoneyFxLock:
    corridor = (
        db.query(CambioPaymentCorridor)
        .filter(CambioPaymentCorridor.corridor_code == body.corridor_code.upper())
        .first()
    )
    if not corridor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="corridor_not_found")

    tx = corridor.transaction_currency
    settle = corridor.settlement_currency
    if tx == settle:
        rate = Decimal("1")
    else:
        fx = fx_service.convert_cents(db, body.amount_cents_ref or 10000, tx, settle)
        rate = fx.get("rate")
        if rate is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fx_rate_not_found")
        rate = Decimal(str(rate))

    spread = int(corridor.default_spread_bps or 0)
    adjusted = rate * (Decimal(1) + Decimal(spread) / Decimal(10000))
    ref = f"LOCK-{body.corridor_code.upper()}-{int(_utcnow().timestamp())}"
    row = MoneyFxLock(
        id=new_id(),
        lock_reference=ref,
        player_code=body.player_code.upper() if body.player_code else None,
        corridor_code=corridor.corridor_code,
        base_currency=corridor.transaction_currency,
        quote_currency=corridor.settlement_currency,
        locked_rate=adjusted,
        spread_bps=spread,
        amount_cents_ref=body.amount_cents_ref,
        status="ACTIVE",
        expires_at=_utcnow() + timedelta(hours=body.ttl_hours),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
