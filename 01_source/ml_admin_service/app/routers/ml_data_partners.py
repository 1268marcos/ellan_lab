from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    MlDataPartnerIn,
    MlDataPartnerListOut,
    MlDataPartnerOut,
    MlDataPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import partner_service

router = APIRouter(prefix="/ml-data-partners", tags=["ml-data-partners"])


@router.get("", response_model=MlDataPartnerListOut)
def list_partners(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> MlDataPartnerListOut:
    partners = partner_service.list_partners(db, active_only=active_only)
    out = [MlDataPartnerOut.model_validate(p) for p in partners]
    return MlDataPartnerListOut(partners=out, total=len(out))


@router.post("", response_model=MlDataPartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: MlDataPartnerIn, db: Session = Depends(get_db)) -> MlDataPartnerOut:
    return MlDataPartnerOut.model_validate(partner_service.create_partner(db, body))


@router.get("/{partner_id}", response_model=MlDataPartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> MlDataPartnerOut:
    return MlDataPartnerOut.model_validate(partner_service.get_partner_or_404(db, partner_id))


@router.patch("/{partner_id}", response_model=MlDataPartnerOut)
def update_partner(
    partner_id: str, body: MlDataPartnerUpdate, db: Session = Depends(get_db)
) -> MlDataPartnerOut:
    return MlDataPartnerOut.model_validate(partner_service.update_partner(db, partner_id, body))


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: str, db: Session = Depends(get_db)) -> None:
    partner_service.delete_partner(db, partner_id)


@router.put("/{partner_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    partner_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return partner_service.configure_webhook(db, partner_id, body)


@router.get("/{partner_id}/webhook", response_model=WebhookOut)
def get_webhook(partner_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = partner_service.get_webhook(db, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{partner_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return partner_service.rotate_api_key(db, partner_id)


@router.get("/{partner_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return partner_service.list_api_keys(db, partner_id)
