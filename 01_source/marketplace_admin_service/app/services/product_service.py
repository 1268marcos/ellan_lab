from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.marketplace import SellerProduct
from app.schemas.marketplace import SellerProductCreateIn, SellerProductUpdateIn
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_products(
    db: Session,
    seller_id: str | None = None,
    locker_id: str | None = None,
) -> list[SellerProduct]:
    q = db.query(SellerProduct).filter(SellerProduct.deleted_at.is_(None))
    if seller_id:
        q = q.filter(SellerProduct.seller_id == seller_id)
    if locker_id:
        q = q.filter(SellerProduct.locker_id == locker_id)
    return q.order_by(SellerProduct.priority).all()


def get_product_or_404(db: Session, product_row_id: str) -> SellerProduct:
    row = (
        db.query(SellerProduct)
        .filter(SellerProduct.id == product_row_id, SellerProduct.deleted_at.is_(None))
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seller_product_not_found")
    return row


def create_product(db: Session, body: SellerProductCreateIn) -> SellerProduct:
    get_seller_or_404(db, body.seller_id)
    exists = (
        db.query(SellerProduct)
        .filter(
            SellerProduct.seller_id == body.seller_id,
            SellerProduct.locker_id == body.locker_id,
            SellerProduct.product_id == body.product_id,
            SellerProduct.deleted_at.is_(None),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="seller_product_exists")
    now = _utcnow()
    row = SellerProduct(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_product(db: Session, product_row_id: str, body: SellerProductUpdateIn) -> SellerProduct:
    row = get_product_or_404(db, product_row_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_product(db: Session, product_row_id: str) -> None:
    row = get_product_or_404(db, product_row_id)
    row.deleted_at = _utcnow()
    row.status = "INACTIVE"
    row.updated_at = _utcnow()
    db.commit()
