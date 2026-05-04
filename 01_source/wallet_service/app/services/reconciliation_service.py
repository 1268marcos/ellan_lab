from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.wallet import Wallet
from app.services import wallet_service


def reconcile_user(db: Session, user_id: str) -> dict:
    settings = get_settings()
    w = db.get(Wallet, user_id)
    if not w:
        return {"user_id": user_id, "ledger_sum": 0, "wallet_balance": 0, "divergent": False, "rolled_back": False}
    ledger = wallet_service.ledger_sum(db, user_id)
    bal = w.balance
    denom = max(abs(ledger), abs(bal), 1)
    rel = abs(ledger - bal) / denom
    divergent = rel > settings.divergence_max
    rolled_back = False
    if divergent:
        w.balance = ledger
        w.version += 1
        db.commit()
        rolled_back = True
    return {
        "user_id": user_id,
        "ledger_sum": ledger,
        "wallet_balance": bal,
        "divergent": divergent,
        "rolled_back": rolled_back,
    }


def reconcile_all(db: Session) -> list[dict]:
    rows = db.query(Wallet).all()
    return [reconcile_user(db, w.user_id) for w in rows]
