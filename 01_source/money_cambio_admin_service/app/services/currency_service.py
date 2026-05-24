from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.money import MoneyCurrencyCatalog
from app.schemas.money import MoneyCurrencyIn, MoneyCurrencyUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_currencies(db: Session, active_only: bool = False) -> list[MoneyCurrencyCatalog]:
    q = db.query(MoneyCurrencyCatalog)
    if active_only:
        q = q.filter(MoneyCurrencyCatalog.is_active.is_(True))
    return q.order_by(MoneyCurrencyCatalog.code).all()


def create_currency(db: Session, body: MoneyCurrencyIn) -> MoneyCurrencyCatalog:
    code = body.code.upper()
    if db.query(MoneyCurrencyCatalog).filter(MoneyCurrencyCatalog.code == code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="currency_code_exists")
    row = MoneyCurrencyCatalog(code=code, **body.model_dump(exclude={"code"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_currency_or_404(db: Session, item_id: int) -> MoneyCurrencyCatalog:
    row = db.get(MoneyCurrencyCatalog, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="currency_not_found")
    return row


def update_currency(db: Session, item_id: int, body: MoneyCurrencyUpdate) -> MoneyCurrencyCatalog:
    row = get_currency_or_404(db, item_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_currency(db: Session, item_id: int) -> None:
    row = get_currency_or_404(db, item_id)
    db.delete(row)
    db.commit()
