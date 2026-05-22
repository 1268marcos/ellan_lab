from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import (
    LockerPaymentMethodIn,
    LockerPaymentMethodListOut,
    LockerPaymentMethodOut,
    LockerPaymentMethodUpdate,
)
from app.services import catalog_service

router = APIRouter(prefix="/locker-payment-methods", tags=["locker-payment-methods"])


@router.get("", response_model=LockerPaymentMethodListOut)
def list_items(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> LockerPaymentMethodListOut:
    items = catalog_service.list_locker_methods(db, locker_id=locker_id)
    out = [LockerPaymentMethodOut.model_validate(i) for i in items]
    return LockerPaymentMethodListOut(items=out, total=len(out))


@router.post("", response_model=LockerPaymentMethodOut, status_code=status.HTTP_201_CREATED)
def upsert_item(body: LockerPaymentMethodIn, db: Session = Depends(get_db)) -> LockerPaymentMethodOut:
    return LockerPaymentMethodOut.model_validate(catalog_service.upsert_locker_method(db, body))


@router.patch("/{locker_id}/{method}", response_model=LockerPaymentMethodOut)
def update_item(
    locker_id: str,
    method: str,
    body: LockerPaymentMethodUpdate,
    db: Session = Depends(get_db),
) -> LockerPaymentMethodOut:
    return LockerPaymentMethodOut.model_validate(
        catalog_service.update_locker_method(db, locker_id, method, body)
    )


@router.delete("/{locker_id}/{method}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(locker_id: str, method: str, db: Session = Depends(get_db)) -> None:
    catalog_service.delete_locker_method(db, locker_id, method)
