from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.gateway_ops import (
    PaymentGatewayDeviceRegistry,
    PaymentGatewayIdempotencyKey,
    PaymentGatewayRiskEvent,
)
from app.schemas.gateway_ops import DeviceRegistryUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_devices(db: Session, limit: int = 100) -> list[PaymentGatewayDeviceRegistry]:
    return (
        db.query(PaymentGatewayDeviceRegistry)
        .order_by(PaymentGatewayDeviceRegistry.last_seen_at_epoch.desc())
        .limit(limit)
        .all()
    )


def get_device_or_404(db: Session, device_hash: str) -> PaymentGatewayDeviceRegistry:
    row = db.get(PaymentGatewayDeviceRegistry, device_hash)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="device_not_found")
    return row


def update_device(db: Session, device_hash: str, body: DeviceRegistryUpdate) -> PaymentGatewayDeviceRegistry:
    row = get_device_or_404(db, device_hash)
    if body.region_code is not None:
        row.region_code = body.region_code
    if body.locker_id is not None:
        row.locker_id = body.locker_id
    if body.flags_json is not None:
        row.flags_json = body.flags_json
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_idempotency(db: Session, limit: int = 100) -> list[PaymentGatewayIdempotencyKey]:
    return (
        db.query(PaymentGatewayIdempotencyKey)
        .order_by(PaymentGatewayIdempotencyKey.created_at_epoch.desc())
        .limit(limit)
        .all()
    )


def get_idempotency_or_404(db: Session, key_id: str) -> PaymentGatewayIdempotencyKey:
    row = db.get(PaymentGatewayIdempotencyKey, key_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="idempotency_not_found")
    return row


def delete_idempotency(db: Session, key_id: str) -> None:
    row = get_idempotency_or_404(db, key_id)
    db.delete(row)
    db.commit()


def purge_expired_idempotency(db: Session) -> int:
    now = int(time.time())
    q = db.query(PaymentGatewayIdempotencyKey).filter(
        PaymentGatewayIdempotencyKey.expires_at_epoch < now
    )
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


def list_risk_events(db: Session, limit: int = 100) -> list[PaymentGatewayRiskEvent]:
    return (
        db.query(PaymentGatewayRiskEvent)
        .order_by(PaymentGatewayRiskEvent.created_at_epoch.desc())
        .limit(limit)
        .all()
    )


def get_risk_event_or_404(db: Session, event_id: str) -> PaymentGatewayRiskEvent:
    row = db.get(PaymentGatewayRiskEvent, event_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="risk_event_not_found")
    return row
