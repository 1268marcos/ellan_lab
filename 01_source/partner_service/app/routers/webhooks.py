from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.webhook import WebhookConfigureIn, WebhookDeliveryOut, WebhookSubscriptionOut
from app.services import partner_service
from app.services import webhook_delivery

router = APIRouter(tags=["webhooks"])


@router.post("/partners/{partner_id}/webhooks", response_model=WebhookSubscriptionOut, status_code=201)
def configure_webhook(
    partner_id: str,
    body: WebhookConfigureIn,
    request: Request,
    db: Session = Depends(get_db),
) -> WebhookSubscriptionOut:
    if not partner_service.get_partner(db, partner_id):
        raise HTTPException(status_code=404, detail="partner not found")
    sub = webhook_delivery.configure_webhook(db, partner_id, body)
    redis = request.app.state.redis_sync
    webhook_delivery.publish_to_stream(
        db,
        redis,
        sub,
        event_type="webhook.configured",
        payload={"hello": "world"},
    )
    events = json.loads(sub.events)
    return WebhookSubscriptionOut(
        id=sub.id,
        partner_id=sub.partner_id,
        url=sub.url,
        events=events,
        is_active=sub.is_active,
        created_at=sub.created_at,
    )


@router.get("/partners/{partner_id}/webhooks/deliveries", response_model=list[WebhookDeliveryOut])
def list_deliveries(partner_id: str, db: Session = Depends(get_db)) -> list[WebhookDeliveryOut]:
    if not partner_service.get_partner(db, partner_id):
        raise HTTPException(status_code=404, detail="partner not found")
    rows = webhook_delivery.list_deliveries(db, partner_id)
    return [WebhookDeliveryOut.model_validate(r) for r in rows]
