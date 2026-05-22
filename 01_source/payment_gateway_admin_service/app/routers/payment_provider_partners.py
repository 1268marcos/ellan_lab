from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.provider import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    PaymentProviderPartnerIn,
    PaymentProviderPartnerListOut,
    PaymentProviderPartnerOut,
    PaymentProviderPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import provider_service

router = APIRouter(prefix="/payment-provider-partners", tags=["payment-provider-partners"])


@router.get("", response_model=PaymentProviderPartnerListOut)
def list_partners(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> PaymentProviderPartnerListOut:
    partners = provider_service.list_providers(db, active_only=active_only)
    out = [PaymentProviderPartnerOut.model_validate(p) for p in partners]
    return PaymentProviderPartnerListOut(partners=out, total=len(out))


@router.post("", response_model=PaymentProviderPartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: PaymentProviderPartnerIn, db: Session = Depends(get_db)) -> PaymentProviderPartnerOut:
    return PaymentProviderPartnerOut.model_validate(provider_service.create_provider(db, body))


@router.get("/{provider_id}", response_model=PaymentProviderPartnerOut)
def get_partner(provider_id: str, db: Session = Depends(get_db)) -> PaymentProviderPartnerOut:
    return PaymentProviderPartnerOut.model_validate(provider_service.get_provider_or_404(db, provider_id))


@router.patch("/{provider_id}", response_model=PaymentProviderPartnerOut)
def update_partner(
    provider_id: str, body: PaymentProviderPartnerUpdate, db: Session = Depends(get_db)
) -> PaymentProviderPartnerOut:
    return PaymentProviderPartnerOut.model_validate(provider_service.update_provider(db, provider_id, body))


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(provider_id: str, db: Session = Depends(get_db)) -> None:
    provider_service.delete_provider(db, provider_id)


@router.put("/{provider_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    provider_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return provider_service.configure_webhook(db, provider_id, body)


@router.get("/{provider_id}/webhook", response_model=WebhookOut)
def get_webhook(provider_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = provider_service.get_webhook(db, provider_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{provider_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(provider_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return provider_service.rotate_api_key(db, provider_id)


@router.get("/{provider_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(provider_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return provider_service.list_api_keys(db, provider_id)
