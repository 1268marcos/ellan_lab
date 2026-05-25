from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.finance import HardwareLockerCapex, HardwareLockerOpex
from app.models.topology import HardwareLockerFeature, HardwareLockerSlot
from app.schemas.finance_topology import HardwareLockerCapexIn, HardwareLockerOpexIn
from app.services.crypto_util import new_id


def list_capex(db: Session, locker_id: str | None = None) -> list[HardwareLockerCapex]:
    q = db.query(HardwareLockerCapex)
    if locker_id:
        q = q.filter(HardwareLockerCapex.locker_id == locker_id)
    return q.order_by(HardwareLockerCapex.depreciation_start_date.desc()).all()


def create_capex(db: Session, body: HardwareLockerCapexIn) -> HardwareLockerCapex:
    row = HardwareLockerCapex(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_opex(db: Session, locker_id: str | None = None) -> list[HardwareLockerOpex]:
    q = db.query(HardwareLockerOpex)
    if locker_id:
        q = q.filter(HardwareLockerOpex.locker_id == locker_id)
    return q.order_by(HardwareLockerOpex.reference_month.desc()).all()


def create_opex(db: Session, body: HardwareLockerOpexIn) -> HardwareLockerOpex:
    row = HardwareLockerOpex(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_features(db: Session, locker_id: str | None = None) -> list[HardwareLockerFeature]:
    q = db.query(HardwareLockerFeature)
    if locker_id:
        q = q.filter(HardwareLockerFeature.locker_id == locker_id)
    return q.all()


def get_feature_or_404(db: Session, locker_id: str) -> HardwareLockerFeature:
    row = db.get(HardwareLockerFeature, locker_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="locker_features_not_found")
    return row


def list_slots(db: Session, locker_id: str | None = None) -> list[HardwareLockerSlot]:
    q = db.query(HardwareLockerSlot)
    if locker_id:
        q = q.filter(HardwareLockerSlot.locker_id == locker_id)
    return q.order_by(HardwareLockerSlot.slot_number).all()
