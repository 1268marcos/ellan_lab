from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_key import ApiKeyListOut, ApiKeyRotateOut
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services import api_key_service, webhook_service

router = APIRouter(prefix="/sellers", tags=["seller-integrations"])


@router.put("/{seller_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    seller_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return webhook_service.configure_webhook(db, seller_id, body)


@router.get("/{seller_id}/webhook", response_model=WebhookOut)
def get_webhook(seller_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = webhook_service.get_webhook(db, seller_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{seller_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(seller_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return api_key_service.rotate_api_key(db, seller_id)


@router.get("/{seller_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(seller_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return api_key_service.list_api_keys(db, seller_id)
