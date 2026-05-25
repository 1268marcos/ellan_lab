from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_topology import (
    HardwareLockerCapexIn,
    HardwareLockerCapexListOut,
    HardwareLockerCapexOut,
    HardwareLockerFeatureListOut,
    HardwareLockerFeatureOut,
    HardwareLockerOpexIn,
    HardwareLockerOpexListOut,
    HardwareLockerOpexOut,
    HardwareLockerSlotListOut,
    HardwareLockerSlotOut,
)
from app.services import finance_topology_service

router = APIRouter(tags=["locker-finance-topology"])


@router.get("/locker-capex", response_model=HardwareLockerCapexListOut)
def list_capex(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerCapexListOut:
    items = finance_topology_service.list_capex(db, locker_id=locker_id)
    out = [HardwareLockerCapexOut.model_validate(i) for i in items]
    return HardwareLockerCapexListOut(items=out, total=len(out))


@router.post("/locker-capex", response_model=HardwareLockerCapexOut, status_code=status.HTTP_201_CREATED)
def create_capex(body: HardwareLockerCapexIn, db: Session = Depends(get_db)) -> HardwareLockerCapexOut:
    return HardwareLockerCapexOut.model_validate(finance_topology_service.create_capex(db, body))


@router.get("/locker-opex", response_model=HardwareLockerOpexListOut)
def list_opex(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerOpexListOut:
    items = finance_topology_service.list_opex(db, locker_id=locker_id)
    out = [HardwareLockerOpexOut.model_validate(i) for i in items]
    return HardwareLockerOpexListOut(items=out, total=len(out))


@router.post("/locker-opex", response_model=HardwareLockerOpexOut, status_code=status.HTTP_201_CREATED)
def create_opex(body: HardwareLockerOpexIn, db: Session = Depends(get_db)) -> HardwareLockerOpexOut:
    return HardwareLockerOpexOut.model_validate(finance_topology_service.create_opex(db, body))


@router.get("/locker-features", response_model=HardwareLockerFeatureListOut)
def list_features(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerFeatureListOut:
    items = finance_topology_service.list_features(db, locker_id=locker_id)
    out = [HardwareLockerFeatureOut.model_validate(i) for i in items]
    return HardwareLockerFeatureListOut(items=out, total=len(out))


@router.get("/locker-features/{locker_id}", response_model=HardwareLockerFeatureOut)
def get_features(locker_id: str, db: Session = Depends(get_db)) -> HardwareLockerFeatureOut:
    return HardwareLockerFeatureOut.model_validate(finance_topology_service.get_feature_or_404(db, locker_id))


@router.get("/locker-slots", response_model=HardwareLockerSlotListOut)
def list_slots(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerSlotListOut:
    items = finance_topology_service.list_slots(db, locker_id=locker_id)
    out = [HardwareLockerSlotOut.model_validate(i) for i in items]
    return HardwareLockerSlotListOut(items=out, total=len(out))
