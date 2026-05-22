from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import (
    PaymentInterfaceCatalogIn,
    PaymentInterfaceCatalogListOut,
    PaymentInterfaceCatalogOut,
    PaymentInterfaceCatalogUpdate,
)
from app.services import catalog_service

router = APIRouter(prefix="/payment-interface-catalog", tags=["payment-interface-catalog"])


@router.get("", response_model=PaymentInterfaceCatalogListOut)
def list_items(active_only: bool = Query(False), db: Session = Depends(get_db)) -> PaymentInterfaceCatalogListOut:
    items = catalog_service.list_interfaces(db, active_only=active_only)
    out = [PaymentInterfaceCatalogOut.model_validate(i) for i in items]
    return PaymentInterfaceCatalogListOut(items=out, total=len(out))


@router.post("", response_model=PaymentInterfaceCatalogOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentInterfaceCatalogIn, db: Session = Depends(get_db)) -> PaymentInterfaceCatalogOut:
    return PaymentInterfaceCatalogOut.model_validate(catalog_service.create_interface(db, body))


@router.patch("/{item_id}", response_model=PaymentInterfaceCatalogOut)
def update_item(
    item_id: int, body: PaymentInterfaceCatalogUpdate, db: Session = Depends(get_db)
) -> PaymentInterfaceCatalogOut:
    return PaymentInterfaceCatalogOut.model_validate(catalog_service.update_interface(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    catalog_service.delete_interface(db, item_id)
