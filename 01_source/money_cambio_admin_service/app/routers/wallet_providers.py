from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import (
    WalletProviderCatalogIn,
    WalletProviderCatalogListOut,
    WalletProviderCatalogOut,
    WalletProviderCatalogUpdate,
)
from app.services import catalog_service

router = APIRouter(prefix="/wallet-provider-catalog", tags=["wallet-providers"])


@router.get("", response_model=WalletProviderCatalogListOut)
def list_items(active_only: bool = Query(False), db: Session = Depends(get_db)) -> WalletProviderCatalogListOut:
    items = catalog_service.list_wallets(db, active_only=active_only)
    out = [WalletProviderCatalogOut.model_validate(i) for i in items]
    return WalletProviderCatalogListOut(items=out, total=len(out))


@router.post("", response_model=WalletProviderCatalogOut, status_code=status.HTTP_201_CREATED)
def create_item(body: WalletProviderCatalogIn, db: Session = Depends(get_db)) -> WalletProviderCatalogOut:
    return WalletProviderCatalogOut.model_validate(catalog_service.create_wallet(db, body))


@router.patch("/{item_id}", response_model=WalletProviderCatalogOut)
def update_item(
    item_id: int, body: WalletProviderCatalogUpdate, db: Session = Depends(get_db)
) -> WalletProviderCatalogOut:
    return WalletProviderCatalogOut.model_validate(catalog_service.update_wallet(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    catalog_service.delete_wallet(db, item_id)
