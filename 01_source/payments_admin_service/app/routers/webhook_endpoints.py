from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import (
    WebhookEndpointIn,
    WebhookEndpointListOut,
    WebhookEndpointOut,
    WebhookEndpointUpdate,
    WebhookSecretRotateOut,
)
from app.services import payments_service

router = APIRouter(prefix="/webhook-endpoints", tags=["webhook-endpoints"])


@router.get("", response_model=WebhookEndpointListOut)
def list_items(
    partner_type: str | None = Query(None),
    partner_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> WebhookEndpointListOut:
    items = payments_service.list_webhooks(
        db, partner_type=partner_type, partner_id=partner_id, limit=limit
    )
    out = [WebhookEndpointOut.model_validate(i) for i in items]
    return WebhookEndpointListOut(items=out, total=len(out))


@router.post("", response_model=WebhookEndpointOut, status_code=status.HTTP_201_CREATED)
def create_item(body: WebhookEndpointIn, db: Session = Depends(get_db)) -> WebhookEndpointOut:
    return WebhookEndpointOut.model_validate(payments_service.create_webhook(db, body))


@router.get("/{item_id}", response_model=WebhookEndpointOut)
def get_item(item_id: str, db: Session = Depends(get_db)) -> WebhookEndpointOut:
    return WebhookEndpointOut.model_validate(payments_service.get_webhook_or_404(db, item_id))


@router.patch("/{item_id}", response_model=WebhookEndpointOut)
def update_item(
    item_id: str, body: WebhookEndpointUpdate, db: Session = Depends(get_db)
) -> WebhookEndpointOut:
    return WebhookEndpointOut.model_validate(payments_service.update_webhook(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_webhook(db, item_id)


@router.post("/{item_id}/rotate-secret", response_model=WebhookSecretRotateOut)
def rotate_secret(item_id: str, db: Session = Depends(get_db)) -> WebhookSecretRotateOut:
    return payments_service.rotate_webhook_secret(db, item_id)
