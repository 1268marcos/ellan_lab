from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.marketplace import SellerReview
from app.schemas.marketplace import SellerReviewCreateIn
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_reviews(db: Session, seller_id: str | None = None) -> list[SellerReview]:
    q = db.query(SellerReview)
    if seller_id:
        q = q.filter(SellerReview.seller_id == seller_id)
    return q.order_by(SellerReview.created_at.desc()).all()


def create_review(db: Session, body: SellerReviewCreateIn) -> SellerReview:
    get_seller_or_404(db, body.seller_id)
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_rating")
    row = SellerReview(id=new_id(), created_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_review(db: Session, review_id: str) -> None:
    row = db.get(SellerReview, review_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review_not_found")
    db.delete(row)
    db.commit()
