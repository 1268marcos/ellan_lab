from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace import SellerCreateIn, SellerListOut, SellerOut, SellerUpdateIn
from app.services import seller_service

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.get("", response_model=SellerListOut)
def list_sellers(active_only: bool = Query(False), db: Session = Depends(get_db)) -> SellerListOut:
    rows = seller_service.list_sellers(db, active_only=active_only)
    out = [SellerOut.model_validate(r) for r in rows]
    return SellerListOut(sellers=out, total=len(out))


@router.post("", response_model=SellerOut, status_code=status.HTTP_201_CREATED)
def create_seller(body: SellerCreateIn, db: Session = Depends(get_db)) -> SellerOut:
    return SellerOut.model_validate(seller_service.create_seller(db, body))


@router.get("/{seller_id}", response_model=SellerOut)
def get_seller(seller_id: str, db: Session = Depends(get_db)) -> SellerOut:
    return SellerOut.model_validate(seller_service.get_seller_or_404(db, seller_id))


@router.patch("/{seller_id}", response_model=SellerOut)
def update_seller(seller_id: str, body: SellerUpdateIn, db: Session = Depends(get_db)) -> SellerOut:
    return SellerOut.model_validate(seller_service.update_seller(db, seller_id, body))


@router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller(seller_id: str, db: Session = Depends(get_db)) -> None:
    seller_service.delete_seller(db, seller_id)
