from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    BiDataPartnerIn,
    BiDataPartnerListOut,
    BiDataPartnerOut,
    BiDataPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import partner_service

router = APIRouter(prefix="/bi-data-partners", tags=["bi-data-partners"])


@router.get("", response_model=BiDataPartnerListOut)
def list_partners(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> BiDataPartnerListOut:
    partners = partner_service.list_partners(db, active_only=active_only)
    return BiDataPartnerListOut(
        partners=[BiDataPartnerOut.model_validate(p) for p in partners],
        total=len(partners),
    )


@router.post("", response_model=BiDataPartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: BiDataPartnerIn, db: Session = Depends(get_db)) -> BiDataPartnerOut:
    return BiDataPartnerOut.model_validate(partner_service.create_partner(db, body))


@router.put("/{partner_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    partner_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return partner_service.configure_webhook(db, partner_id, body)


@router.post("/{partner_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return partner_service.rotate_api_key(db, partner_id)


@router.get("/{partner_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return partner_service.list_api_keys(db, partner_id)


@router.get("/{partner_id}/webhook", response_model=WebhookOut)
def get_webhook(partner_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = partner_service.get_webhook(db, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row
