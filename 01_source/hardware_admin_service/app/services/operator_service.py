from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.operators import LockerOperator
from app.schemas.operators import LockerOperatorIn, LockerOperatorUpdate
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_operators(db: Session, active_only: bool = False) -> list[LockerOperator]:
    q = db.query(LockerOperator)
    if active_only:
        q = q.filter(LockerOperator.active.is_(True))
    return q.order_by(LockerOperator.name).all()


def get_operator_or_404(db: Session, operator_id: str) -> LockerOperator:
    row = db.get(LockerOperator, operator_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="operator_not_found")
    return row


def create_operator(db: Session, body: LockerOperatorIn) -> LockerOperator:
    oid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    row = LockerOperator(id=oid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_operator(db: Session, operator_id: str, body: LockerOperatorUpdate) -> LockerOperator:
    row = get_operator_or_404(db, operator_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_operator(db: Session, operator_id: str) -> None:
    row = get_operator_or_404(db, operator_id)
    db.delete(row)
    db.commit()
