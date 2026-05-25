from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assets import HardwareAsset
from app.schemas.assets import HardwareAssetIn, HardwareAssetUpdate
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_assets(db: Session, locker_id: str | None = None, vendor_id: str | None = None) -> list[HardwareAsset]:
    q = db.query(HardwareAsset)
    if locker_id:
        q = q.filter(HardwareAsset.locker_id == locker_id)
    if vendor_id:
        q = q.filter(HardwareAsset.vendor_id == vendor_id)
    return q.order_by(HardwareAsset.asset_code).all()


def get_asset_or_404(db: Session, asset_id: str) -> HardwareAsset:
    row = db.get(HardwareAsset, asset_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="asset_not_found")
    return row


def create_asset(db: Session, body: HardwareAssetIn) -> HardwareAsset:
    if db.query(HardwareAsset).filter(HardwareAsset.asset_code == body.asset_code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="asset_code_exists")
    aid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    row = HardwareAsset(id=aid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_asset(db: Session, asset_id: str, body: HardwareAssetUpdate) -> HardwareAsset:
    row = get_asset_or_404(db, asset_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_asset(db: Session, asset_id: str) -> None:
    row = get_asset_or_404(db, asset_id)
    db.delete(row)
    db.commit()
