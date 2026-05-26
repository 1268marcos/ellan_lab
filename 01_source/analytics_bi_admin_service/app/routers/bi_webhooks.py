from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_webhooks import BiCapabilityWebhookIn, BiCapabilityWebhookListOut, BiCapabilityWebhookOut
from app.services import bi_webhooks_service

router = APIRouter(prefix="/bi-capability-webhooks", tags=["bi-webhooks"])


@router.get("", response_model=BiCapabilityWebhookListOut)
def list_webhooks(db: Session = Depends(get_db)) -> BiCapabilityWebhookListOut:
    rows = bi_webhooks_service.list_webhooks(db)
    webhooks = [BiCapabilityWebhookOut.model_validate(bi_webhooks_service.webhook_out(r)) for r in rows]
    return BiCapabilityWebhookListOut(webhooks=webhooks, total=len(webhooks))


@router.post("", response_model=BiCapabilityWebhookOut, status_code=status.HTTP_201_CREATED)
def create_webhook(body: BiCapabilityWebhookIn, db: Session = Depends(get_db)) -> BiCapabilityWebhookOut:
    row = bi_webhooks_service.create_webhook(db, body)
    return BiCapabilityWebhookOut.model_validate(bi_webhooks_service.webhook_out(row))
