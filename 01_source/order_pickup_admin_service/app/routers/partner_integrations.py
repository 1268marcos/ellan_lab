from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_key import ApiKeyListOut, ApiKeyRotateOut
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services import api_key_service, webhook_service

router = APIRouter(prefix="/partners", tags=["partner-integrations"])


@router.put("/{partner_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    partner_id: str,
    body: WebhookConfigureIn,
    partner_type: str = Query(..., description="ECOMMERCE ou LOGISTICS"),
    db: Session = Depends(get_db),
) -> WebhookOut:
    return webhook_service.configure_webhook(db, partner_id, partner_type, body)


@router.get("/{partner_id}/webhook", response_model=WebhookOut)
def get_webhook(
    partner_id: str,
    partner_type: str = Query(...),
    db: Session = Depends(get_db),
) -> WebhookOut:
    row = webhook_service.get_webhook(db, partner_id, partner_type)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{partner_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(
    partner_id: str,
    partner_type: str = Query(...),
    db: Session = Depends(get_db),
) -> ApiKeyRotateOut:
    return api_key_service.rotate_api_key(db, partner_id, partner_type)


@router.get("/{partner_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(
    partner_id: str,
    partner_type: str = Query(...),
    db: Session = Depends(get_db),
) -> ApiKeyListOut:
    return api_key_service.list_api_keys(db, partner_id, partner_type)
