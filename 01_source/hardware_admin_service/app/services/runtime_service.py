from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.hardware_ops import HardwareSyncQueue, HardwareTelemetryEvent
from app.models.runtime import HardwareDeviceRegistry, RuntimeLocker
from app.schemas.runtime import RuntimeLockerIn, RuntimeLockerUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_runtime_lockers(db: Session, vendor_id: str | None = None) -> list[RuntimeLocker]:
    q = db.query(RuntimeLocker)
    if vendor_id:
        q = q.filter(RuntimeLocker.vendor_id == vendor_id)
    return q.order_by(RuntimeLocker.locker_id).all()


def get_runtime_locker_or_404(db: Session, locker_id: str) -> RuntimeLocker:
    row = db.get(RuntimeLocker, locker_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runtime_locker_not_found")
    return row


def create_runtime_locker(db: Session, body: RuntimeLockerIn) -> RuntimeLocker:
    if db.get(RuntimeLocker, body.locker_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="locker_id_exists")
    row = RuntimeLocker(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_runtime_locker(db: Session, locker_id: str, body: RuntimeLockerUpdate) -> RuntimeLocker:
    row = get_runtime_locker_or_404(db, locker_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_runtime_locker(db: Session, locker_id: str) -> None:
    row = get_runtime_locker_or_404(db, locker_id)
    db.delete(row)
    db.commit()


def list_devices(db: Session, locker_id: str | None = None) -> list[HardwareDeviceRegistry]:
    q = db.query(HardwareDeviceRegistry)
    if locker_id:
        q = q.filter(HardwareDeviceRegistry.locker_id == locker_id)
    return q.order_by(HardwareDeviceRegistry.last_seen_at_epoch.desc()).all()


def list_sync_queue(db: Session, status_filter: str | None = None) -> list[HardwareSyncQueue]:
    q = db.query(HardwareSyncQueue)
    if status_filter:
        q = q.filter(HardwareSyncQueue.status == status_filter)
    return q.order_by(HardwareSyncQueue.created_at.desc()).all()


def list_telemetry(db: Session, locker_id: str | None = None) -> list[HardwareTelemetryEvent]:
    q = db.query(HardwareTelemetryEvent)
    if locker_id:
        q = q.filter(HardwareTelemetryEvent.locker_id == locker_id)
    return q.order_by(HardwareTelemetryEvent.created_at_epoch.desc()).limit(200).all()
