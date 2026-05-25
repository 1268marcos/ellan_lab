from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.runtime import (
    HardwareDeviceRegistryListOut,
    HardwareDeviceRegistryOut,
    HardwareSyncQueueListOut,
    HardwareSyncQueueOut,
    HardwareTelemetryEventOut,
    HardwareTelemetryListOut,
    RuntimeLockerIn,
    RuntimeLockerListOut,
    RuntimeLockerOut,
    RuntimeLockerUpdate,
)
from app.services import runtime_reconcile_service
from app.services import runtime_service

router = APIRouter(prefix="/runtime-lockers", tags=["runtime-lockers"])


@router.get("", response_model=RuntimeLockerListOut)
def list_runtime_lockers(
    vendor_id: str | None = Query(None), db: Session = Depends(get_db)
) -> RuntimeLockerListOut:
    items = runtime_service.list_runtime_lockers(db, vendor_id=vendor_id)
    out = [RuntimeLockerOut.model_validate(i) for i in items]
    return RuntimeLockerListOut(items=out, total=len(out))


@router.post("", response_model=RuntimeLockerOut, status_code=status.HTTP_201_CREATED)
def create_runtime_locker(body: RuntimeLockerIn, db: Session = Depends(get_db)) -> RuntimeLockerOut:
    return RuntimeLockerOut.model_validate(runtime_service.create_runtime_locker(db, body))


@router.get("/reconcile/diff")
def runtime_reconcile_diff(db: Session = Depends(get_db)) -> dict:
    return runtime_reconcile_service.reconcile_runtime(db)


@router.post("/reconcile/pull")
def runtime_reconcile_pull(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> dict:
    return runtime_reconcile_service.pull_from_runtime(db, locker_id=locker_id)


@router.post("/reconcile/push")
def runtime_reconcile_push(
    locker_id: str | None = Query(None),
    enqueue_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> dict:
    return runtime_reconcile_service.push_to_runtime(db, locker_id=locker_id, enqueue_only=enqueue_only)


@router.get("/{locker_id}", response_model=RuntimeLockerOut)
def get_runtime_locker(locker_id: str, db: Session = Depends(get_db)) -> RuntimeLockerOut:
    return RuntimeLockerOut.model_validate(runtime_service.get_runtime_locker_or_404(db, locker_id))


@router.patch("/{locker_id}", response_model=RuntimeLockerOut)
def update_runtime_locker(
    locker_id: str, body: RuntimeLockerUpdate, db: Session = Depends(get_db)
) -> RuntimeLockerOut:
    return RuntimeLockerOut.model_validate(runtime_service.update_runtime_locker(db, locker_id, body))


@router.delete("/{locker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_runtime_locker(locker_id: str, db: Session = Depends(get_db)) -> None:
    runtime_service.delete_runtime_locker(db, locker_id)


hardware_ops_router = APIRouter(prefix="/hardware-ops", tags=["hardware-ops"])


@hardware_ops_router.get("/devices", response_model=HardwareDeviceRegistryListOut)
def list_devices(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareDeviceRegistryListOut:
    items = runtime_service.list_devices(db, locker_id=locker_id)
    out = [HardwareDeviceRegistryOut.model_validate(i) for i in items]
    return HardwareDeviceRegistryListOut(items=out, total=len(out))


@hardware_ops_router.get("/sync-queue", response_model=HardwareSyncQueueListOut)
def list_sync_queue(
    status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db)
) -> HardwareSyncQueueListOut:
    items = runtime_service.list_sync_queue(db, status_filter=status_filter)
    out = [HardwareSyncQueueOut.model_validate(i) for i in items]
    return HardwareSyncQueueListOut(items=out, total=len(out))


@hardware_ops_router.get("/telemetry", response_model=HardwareTelemetryListOut)
def list_telemetry(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareTelemetryListOut:
    items = runtime_service.list_telemetry(db, locker_id=locker_id)
    out = [HardwareTelemetryEventOut.model_validate(i) for i in items]
    return HardwareTelemetryListOut(items=out, total=len(out))
