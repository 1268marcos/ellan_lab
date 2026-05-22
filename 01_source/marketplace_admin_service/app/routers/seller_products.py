from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace import (
    SellerProductCreateIn,
    SellerProductListOut,
    SellerProductOut,
    SellerProductUpdateIn,
)
from app.services import product_service

router = APIRouter(prefix="/seller-products", tags=["seller-products"])


@router.get("", response_model=SellerProductListOut)
def list_products(
    seller_id: str | None = Query(None),
    locker_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> SellerProductListOut:
    rows = product_service.list_products(db, seller_id=seller_id, locker_id=locker_id)
    out = [SellerProductOut.model_validate(r) for r in rows]
    return SellerProductListOut(products=out, total=len(out))


@router.post("", response_model=SellerProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: SellerProductCreateIn, db: Session = Depends(get_db)) -> SellerProductOut:
    return SellerProductOut.model_validate(product_service.create_product(db, body))


@router.patch("/{product_id}", response_model=SellerProductOut)
def update_product(
    product_id: str, body: SellerProductUpdateIn, db: Session = Depends(get_db)
) -> SellerProductOut:
    return SellerProductOut.model_validate(product_service.update_product(db, product_id, body))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, db: Session = Depends(get_db)) -> None:
    product_service.delete_product(db, product_id)
