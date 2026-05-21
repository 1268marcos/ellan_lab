from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.locker import (
    LockerBulkCreateIn,
    LockerBulkCreateOut,
    LockerCreateIn,
    LockerListOut,
    LockerOut,
    LockerUpdateIn,
)
from app.services import locker_service

router = APIRouter(prefix="/lockers", tags=["lockers"])


@router.get("", response_model=LockerListOut)
def list_lockers(
    region: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> LockerListOut:
    lockers = locker_service.list_lockers(db, region=region, active_only=active_only)
    return LockerListOut(lockers=lockers, total=len(lockers))


@router.post("", response_model=LockerOut, status_code=status.HTTP_201_CREATED)
def create_locker(body: LockerCreateIn, db: Session = Depends(get_db)) -> LockerOut:
    return locker_service.create_locker(db, body)


@router.post("/bulk", response_model=LockerBulkCreateOut, status_code=status.HTTP_201_CREATED)
def bulk_create(body: LockerBulkCreateIn, db: Session = Depends(get_db)) -> LockerBulkCreateOut:
    created, failed = locker_service.bulk_create(db, body)
    return LockerBulkCreateOut(created=created, failed=failed)


@router.get("/{locker_id}", response_model=LockerOut)
def get_locker(locker_id: str, db: Session = Depends(get_db)) -> LockerOut:
    locker = locker_service.get_locker_or_404(db, locker_id)
    return locker_service.locker_to_out(locker)


@router.patch("/{locker_id}", response_model=LockerOut)
def update_locker(locker_id: str, body: LockerUpdateIn, db: Session = Depends(get_db)) -> LockerOut:
    return locker_service.update_locker(db, locker_id, body)


@router.delete("/{locker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_locker(locker_id: str, db: Session = Depends(get_db)) -> None:
    locker_service.delete_locker(db, locker_id)
