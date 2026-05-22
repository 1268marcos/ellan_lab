from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.gateway_ops import (
    DeviceRegistryListOut,
    DeviceRegistryOut,
    DeviceRegistryUpdate,
    IdempotencyKeyListOut,
    IdempotencyKeyOut,
    RiskEventListOut,
    RiskEventOut,
)
from app.services import gateway_ops_service

router = APIRouter(prefix="/gateway-ops", tags=["gateway-ops"])


@router.get("/devices", response_model=DeviceRegistryListOut)
def list_devices(limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> DeviceRegistryListOut:
    items = gateway_ops_service.list_devices(db, limit=limit)
    out = [DeviceRegistryOut.model_validate(i) for i in items]
    return DeviceRegistryListOut(items=out, total=len(out))


@router.patch("/devices/{device_hash}", response_model=DeviceRegistryOut)
def update_device(
    device_hash: str, body: DeviceRegistryUpdate, db: Session = Depends(get_db)
) -> DeviceRegistryOut:
    return DeviceRegistryOut.model_validate(gateway_ops_service.update_device(db, device_hash, body))


@router.get("/idempotency-keys", response_model=IdempotencyKeyListOut)
def list_idempotency(
    limit: int = Query(100, le=500), db: Session = Depends(get_db)
) -> IdempotencyKeyListOut:
    items = gateway_ops_service.list_idempotency(db, limit=limit)
    out = [IdempotencyKeyOut.model_validate(i) for i in items]
    return IdempotencyKeyListOut(items=out, total=len(out))


@router.delete("/idempotency-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idempotency(key_id: str, db: Session = Depends(get_db)) -> None:
    gateway_ops_service.delete_idempotency(db, key_id)


@router.post("/idempotency-keys/purge-expired")
def purge_expired(db: Session = Depends(get_db)) -> dict[str, int]:
    return {"purged": gateway_ops_service.purge_expired_idempotency(db)}


@router.get("/risk-events", response_model=RiskEventListOut)
def list_risk(limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> RiskEventListOut:
    items = gateway_ops_service.list_risk_events(db, limit=limit)
    out = [RiskEventOut.model_validate(i) for i in items]
    return RiskEventListOut(items=out, total=len(out))


@router.get("/risk-events/{event_id}", response_model=RiskEventOut)
def get_risk(event_id: str, db: Session = Depends(get_db)) -> RiskEventOut:
    return RiskEventOut.model_validate(gateway_ops_service.get_risk_event_or_404(db, event_id))
