from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ecosystem import CapabilityProfileWebhookDelivery
from app.models.integration import CapabilityProfileWebhook
from app.schemas.common import ListOut
from app.services.crypto_util import new_id

router = APIRouter(prefix="/webhooks", tags=["deliveries"])


@router.get("/deliveries", response_model=ListOut)
def list_deliveries(
    webhook_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    dead_letter_only: bool = False,
    db: Session = Depends(get_db),
) -> ListOut:
    q = db.query(CapabilityProfileWebhookDelivery).order_by(CapabilityProfileWebhookDelivery.created_at.desc())
    if webhook_id:
        q = q.filter(CapabilityProfileWebhookDelivery.webhook_id == webhook_id)
    if status_filter:
        q = q.filter(CapabilityProfileWebhookDelivery.status == status_filter)
    if dead_letter_only:
        q = q.filter(CapabilityProfileWebhookDelivery.dead_lettered_at.isnot(None))
    items = q.limit(200).all()
    return ListOut(
        items=[
            {
                "id": d.id,
                "webhook_id": d.webhook_id,
                "event_type": d.event_type,
                "http_status": d.http_status,
                "success": d.success,
                "status": d.status,
                "attempt_count": d.attempt_count,
                "dead_lettered_at": d.dead_lettered_at.isoformat() if d.dead_lettered_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in items
        ],
        total=len(items),
    )


@router.post("/deliveries/{delivery_id}/replay")
def replay_delivery(delivery_id: str, db: Session = Depends(get_db)):
    row = db.get(CapabilityProfileWebhookDelivery, delivery_id)
    if not row:
        raise HTTPException(status_code=404, detail="delivery_not_found")
    wh = db.get(CapabilityProfileWebhook, row.webhook_id)
    if not wh:
        raise HTTPException(status_code=404, detail="webhook_not_found")
    replay = CapabilityProfileWebhookDelivery(
        id=new_id(),
        webhook_id=row.webhook_id,
        event_type=row.event_type,
        payload_json=row.payload_json,
        status="REPLAY",
        attempt_count=row.attempt_count + 1,
        success=False,
    )
    db.add(replay)
    db.commit()
    return {"replayed_from": delivery_id, "new_delivery_id": replay.id}
