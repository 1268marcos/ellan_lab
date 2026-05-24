from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import (
    PaymentMethodUiAliasIn,
    PaymentMethodUiAliasListOut,
    PaymentMethodUiAliasOut,
    PaymentMethodUiAliasUpdate,
)
from app.services import catalog_service

router = APIRouter(prefix="/payment-method-ui-alias", tags=["payment-method-ui-alias"])


@router.get("", response_model=PaymentMethodUiAliasListOut)
def list_items(active_only: bool = Query(False), db: Session = Depends(get_db)) -> PaymentMethodUiAliasListOut:
    items = catalog_service.list_aliases(db, active_only=active_only)
    out = [PaymentMethodUiAliasOut.model_validate(i) for i in items]
    return PaymentMethodUiAliasListOut(items=out, total=len(out))


@router.post("", response_model=PaymentMethodUiAliasOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentMethodUiAliasIn, db: Session = Depends(get_db)) -> PaymentMethodUiAliasOut:
    return PaymentMethodUiAliasOut.model_validate(catalog_service.create_alias(db, body))


@router.patch("/{alias_id}", response_model=PaymentMethodUiAliasOut)
def update_item(
    alias_id: str, body: PaymentMethodUiAliasUpdate, db: Session = Depends(get_db)
) -> PaymentMethodUiAliasOut:
    return PaymentMethodUiAliasOut.model_validate(catalog_service.update_alias(db, alias_id, body))


@router.delete("/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(alias_id: str, db: Session = Depends(get_db)) -> None:
    catalog_service.delete_alias(db, alias_id)
