from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assets import HardwareAssetIn, HardwareAssetListOut, HardwareAssetOut, HardwareAssetUpdate
from app.services import asset_service

router = APIRouter(prefix="/hardware-assets", tags=["hardware-assets"])


@router.get("", response_model=HardwareAssetListOut)
def list_assets(
    locker_id: str | None = Query(None),
    vendor_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HardwareAssetListOut:
    items = asset_service.list_assets(db, locker_id=locker_id, vendor_id=vendor_id)
    out = [HardwareAssetOut.model_validate(i) for i in items]
    return HardwareAssetListOut(items=out, total=len(out))


@router.post("", response_model=HardwareAssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(body: HardwareAssetIn, db: Session = Depends(get_db)) -> HardwareAssetOut:
    return HardwareAssetOut.model_validate(asset_service.create_asset(db, body))


@router.get("/{asset_id}", response_model=HardwareAssetOut)
def get_asset(asset_id: str, db: Session = Depends(get_db)) -> HardwareAssetOut:
    return HardwareAssetOut.model_validate(asset_service.get_asset_or_404(db, asset_id))


@router.patch("/{asset_id}", response_model=HardwareAssetOut)
def update_asset(
    asset_id: str, body: HardwareAssetUpdate, db: Session = Depends(get_db)
) -> HardwareAssetOut:
    return HardwareAssetOut.model_validate(asset_service.update_asset(db, asset_id, body))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: str, db: Session = Depends(get_db)) -> None:
    asset_service.delete_asset(db, asset_id)
