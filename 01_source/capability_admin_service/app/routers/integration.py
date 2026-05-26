from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.integration import CapabilityProfileWebhook
from app.schemas.common import ApiKeyRotateOut, ListOut, WebhookIn, WebhookOut
from app.services import integration_service

router = APIRouter(tags=["integration"])


@router.get("/webhooks", response_model=ListOut)
def list_webhooks(profile_id: int | None = None, db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityProfileWebhook)
    if profile_id:
        q = q.filter(CapabilityProfileWebhook.profile_id == profile_id)
    items = q.order_by(CapabilityProfileWebhook.profile_code).all()
    return ListOut(items=[WebhookOut.model_validate(i) for i in items], total=len(items))


@router.put("/webhooks", response_model=WebhookOut)
def upsert_webhook(body: WebhookIn, db: Session = Depends(get_db)) -> WebhookOut:
    return WebhookOut.model_validate(integration_service.configure_webhook(db, body))


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, db: Session = Depends(get_db)):
    return await integration_service.test_webhook(db, webhook_id)


@router.post("/profiles/{profile_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(profile_id: int, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return integration_service.rotate_api_key(db, profile_id)
