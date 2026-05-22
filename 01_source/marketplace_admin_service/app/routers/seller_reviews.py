from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace import SellerReviewCreateIn, SellerReviewListOut, SellerReviewOut
from app.services import review_service

router = APIRouter(prefix="/seller-reviews", tags=["seller-reviews"])


@router.get("", response_model=SellerReviewListOut)
def list_reviews(seller_id: str | None = Query(None), db: Session = Depends(get_db)) -> SellerReviewListOut:
    rows = review_service.list_reviews(db, seller_id=seller_id)
    out = [SellerReviewOut.model_validate(r) for r in rows]
    return SellerReviewListOut(reviews=out, total=len(out))


@router.post("", response_model=SellerReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(body: SellerReviewCreateIn, db: Session = Depends(get_db)) -> SellerReviewOut:
    return SellerReviewOut.model_validate(review_service.create_review(db, body))


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, db: Session = Depends(get_db)) -> None:
    review_service.delete_review(db, review_id)
