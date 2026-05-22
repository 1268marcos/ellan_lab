from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceSeller
from app.schemas.marketplace import SellerCreateIn, SellerUpdateIn
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_sellers(db: Session, active_only: bool = False) -> list[MarketplaceSeller]:
    q = db.query(MarketplaceSeller).filter(MarketplaceSeller.deleted_at.is_(None))
    if active_only:
        q = q.filter(MarketplaceSeller.status == "ACTIVE")
    return q.order_by(MarketplaceSeller.legal_name).all()


def get_seller_or_404(db: Session, seller_id: str) -> MarketplaceSeller:
    row = (
        db.query(MarketplaceSeller)
        .filter(MarketplaceSeller.id == seller_id, MarketplaceSeller.deleted_at.is_(None))
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seller_not_found")
    return row


def create_seller(db: Session, body: SellerCreateIn) -> MarketplaceSeller:
    if db.query(MarketplaceSeller).filter(MarketplaceSeller.tax_id == body.tax_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="tax_id_exists")
    now = _utcnow()
    row = MarketplaceSeller(
        id=new_id(),
        joined_at=now,
        created_at=now,
        updated_at=now,
        **body.model_dump(),
    )
    if row.status == "ACTIVE":
        row.approved_at = now
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_seller(db: Session, seller_id: str, body: SellerUpdateIn) -> MarketplaceSeller:
    row = get_seller_or_404(db, seller_id)
    now = _utcnow()
    data = body.model_dump(exclude_unset=True)
    new_status = data.pop("status", None)
    for k, v in data.items():
        setattr(row, k, v)
    if new_status:
        row.status = new_status
        if new_status == "ACTIVE" and not row.approved_at:
            row.approved_at = now
        if new_status == "SUSPENDED":
            row.suspended_at = now
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return row


def delete_seller(db: Session, seller_id: str) -> None:
    row = get_seller_or_404(db, seller_id)
    row.deleted_at = _utcnow()
    row.status = "INACTIVE"
    row.updated_at = _utcnow()
    db.commit()
