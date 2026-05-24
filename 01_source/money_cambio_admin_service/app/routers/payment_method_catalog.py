from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import (
    PaymentMethodCatalogIn,
    PaymentMethodCatalogListOut,
    PaymentMethodCatalogOut,
    PaymentMethodCatalogUpdate,
)
from app.services import catalog_service

router = APIRouter(prefix="/payment-method-catalog", tags=["payment-method-catalog"])


@router.get("", response_model=PaymentMethodCatalogListOut)
def list_items(active_only: bool = Query(False), db: Session = Depends(get_db)) -> PaymentMethodCatalogListOut:
    items = catalog_service.list_methods(db, active_only=active_only)
    out = [PaymentMethodCatalogOut.model_validate(i) for i in items]
    return PaymentMethodCatalogListOut(items=out, total=len(out))


@router.post("", response_model=PaymentMethodCatalogOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentMethodCatalogIn, db: Session = Depends(get_db)) -> PaymentMethodCatalogOut:
    return PaymentMethodCatalogOut.model_validate(catalog_service.create_method(db, body))


@router.get("/{item_id}", response_model=PaymentMethodCatalogOut)
def get_item(item_id: int, db: Session = Depends(get_db)) -> PaymentMethodCatalogOut:
    return PaymentMethodCatalogOut.model_validate(catalog_service.get_method_or_404(db, item_id))


@router.patch("/{item_id}", response_model=PaymentMethodCatalogOut)
def update_item(
    item_id: int, body: PaymentMethodCatalogUpdate, db: Session = Depends(get_db)
) -> PaymentMethodCatalogOut:
    return PaymentMethodCatalogOut.model_validate(catalog_service.update_method(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    catalog_service.delete_method(db, item_id)
