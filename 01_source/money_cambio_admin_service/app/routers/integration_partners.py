from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.integration import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    IntegrationPartnerIn,
    IntegrationPartnerListOut,
    IntegrationPartnerOut,
    IntegrationPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import integration_service

router = APIRouter(prefix="/integration-partners", tags=["integration-partners"])


@router.get("", response_model=IntegrationPartnerListOut)
def list_partners(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> IntegrationPartnerListOut:
    partners = integration_service.list_partners(db, active_only=active_only)
    out = [IntegrationPartnerOut.model_validate(p) for p in partners]
    return IntegrationPartnerListOut(partners=out, total=len(out))


@router.post("", response_model=IntegrationPartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: IntegrationPartnerIn, db: Session = Depends(get_db)) -> IntegrationPartnerOut:
    return IntegrationPartnerOut.model_validate(integration_service.create_partner(db, body))


@router.get("/{partner_id}", response_model=IntegrationPartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> IntegrationPartnerOut:
    return IntegrationPartnerOut.model_validate(integration_service.get_partner_or_404(db, partner_id))


@router.patch("/{partner_id}", response_model=IntegrationPartnerOut)
def update_partner(
    partner_id: str, body: IntegrationPartnerUpdate, db: Session = Depends(get_db)
) -> IntegrationPartnerOut:
    return IntegrationPartnerOut.model_validate(integration_service.update_partner(db, partner_id, body))


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: str, db: Session = Depends(get_db)) -> None:
    integration_service.delete_partner(db, partner_id)


@router.put("/{partner_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    partner_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return integration_service.configure_webhook(db, partner_id, body)


@router.get("/{partner_id}/webhook", response_model=WebhookOut)
def get_webhook(partner_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = integration_service.get_webhook(db, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{partner_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return integration_service.rotate_api_key(db, partner_id)


@router.get("/{partner_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return integration_service.list_api_keys(db, partner_id)
