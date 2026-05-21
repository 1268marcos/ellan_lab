from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services import webhook_service

router = APIRouter(prefix="/lockers", tags=["webhooks"])


@router.put("/{locker_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    locker_id: str,
    body: WebhookConfigureIn,
    db: Session = Depends(get_db),
) -> WebhookOut:
    return webhook_service.configure_webhook(db, locker_id, body)


@router.get("/{locker_id}/webhook", response_model=WebhookOut)
def get_webhook(locker_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = webhook_service.get_webhook(db, locker_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row
