from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner_capability_webhook import (
    CapabilityWebhookConfigureIn,
    CapabilityWebhookDeliveryListOut,
    CapabilityWebhookDeliveryOut,
    CapabilityWebhookListOut,
    CapabilityWebhookMirrorOut,
    CapabilityWebhookOut,
    DeadLetterReplayBatchOut,
)
from app.services import partner_capability_webhook_service as svc

EVENT_TEST_PING = svc.EVENT_TEST_PING

router = APIRouter(prefix="/ecosystem/capability-webhooks", tags=["partner-capability-webhooks"])
ingress_router = APIRouter(prefix="/webhooks/ingress", tags=["partner-webhook-ingress"])


@router.get("", response_model=CapabilityWebhookListOut)
def list_webhooks(
    ecosystem_player_id: str | None = Query(None),
    player_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CapabilityWebhookListOut:
    rows = svc.list_capability_webhooks(db, ecosystem_player_id=ecosystem_player_id, player_code=player_code)
    return CapabilityWebhookListOut(
        items=[CapabilityWebhookOut.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.put("", response_model=CapabilityWebhookOut)
def upsert_webhook(body: CapabilityWebhookConfigureIn, db: Session = Depends(get_db)) -> CapabilityWebhookOut:
    row = svc.configure_capability_webhook(
        db,
        ecosystem_player_id=body.ecosystem_player_id,
        capability_code=body.capability_code,
        url=body.url,
        secret=body.secret,
        events=body.events,
        source="MANUAL",
        active=body.active,
    )
    return CapabilityWebhookOut.model_validate(row)


@router.post("/mirror-from-capabilities", response_model=CapabilityWebhookMirrorOut)
def mirror_webhooks(db: Session = Depends(get_db)) -> CapabilityWebhookMirrorOut:
    return CapabilityWebhookMirrorOut(**svc.mirror_webhooks_from_capabilities(db))


@router.post("/{webhook_id}/test", response_model=CapabilityWebhookDeliveryOut)
def test_webhook(webhook_id: str, db: Session = Depends(get_db)) -> CapabilityWebhookDeliveryOut:
    d = svc.test_capability_webhook(db, webhook_id)
    return CapabilityWebhookDeliveryOut.model_validate(d)


@router.get("/deliveries", response_model=CapabilityWebhookDeliveryListOut)
def list_deliveries(
    status: str | None = Query(None, description="DELIVERED, FAILED, DEAD_LETTER, SKIPPED"),
    webhook_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> CapabilityWebhookDeliveryListOut:
    rows = svc.list_deliveries(db, status=status, webhook_id=webhook_id, limit=limit)
    items = [CapabilityWebhookDeliveryOut.model_validate(r) for r in rows]
    return CapabilityWebhookDeliveryListOut(items=items, total=len(items))


@router.post("/deliveries/{delivery_id}/replay", response_model=CapabilityWebhookDeliveryOut)
def replay_delivery(delivery_id: str, db: Session = Depends(get_db)) -> CapabilityWebhookDeliveryOut:
    d = svc.replay_delivery(db, delivery_id)
    return CapabilityWebhookDeliveryOut.model_validate(d)


@router.post("/deliveries/replay-dead-letter", response_model=DeadLetterReplayBatchOut)
def replay_dead_letter_batch(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DeadLetterReplayBatchOut:
    return DeadLetterReplayBatchOut(**svc.replay_dead_letter_batch(db, limit=limit))


@ingress_router.post("/{player_code}/{capability_code}")
async def webhook_ingress(
    player_code: str,
    capability_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Receiver interno — registra entrega e aceita POST dos testes."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    event = request.headers.get("X-Ellan-Event") or EVENT_TEST_PING
    hooks = svc.list_capability_webhooks(db, player_code=player_code)
    hook = next((h for h in hooks if h.capability_code == capability_code.upper()), None)
    if hook:
        svc.deliver_event(
            db,
            hook,
            event,
            {"ingress": True, "received": body},
            force=True,
        )
    return {"ok": True, "player_code": player_code, "capability_code": capability_code}
