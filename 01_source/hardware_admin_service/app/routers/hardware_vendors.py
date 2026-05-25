from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vendor import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    HardwareVendorPartnerIn,
    HardwareVendorPartnerListOut,
    HardwareVendorPartnerOut,
    HardwareVendorPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import vendor_service

router = APIRouter(prefix="/hardware-vendors", tags=["hardware-vendors"])


@router.get("", response_model=HardwareVendorPartnerListOut)
def list_vendors(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> HardwareVendorPartnerListOut:
    vendors = vendor_service.list_vendors(db, active_only=active_only)
    out = [HardwareVendorPartnerOut.model_validate(v) for v in vendors]
    return HardwareVendorPartnerListOut(vendors=out, total=len(out))


@router.post("", response_model=HardwareVendorPartnerOut, status_code=status.HTTP_201_CREATED)
def create_vendor(body: HardwareVendorPartnerIn, db: Session = Depends(get_db)) -> HardwareVendorPartnerOut:
    return HardwareVendorPartnerOut.model_validate(vendor_service.create_vendor(db, body))


@router.get("/{vendor_id}", response_model=HardwareVendorPartnerOut)
def get_vendor(vendor_id: str, db: Session = Depends(get_db)) -> HardwareVendorPartnerOut:
    return HardwareVendorPartnerOut.model_validate(vendor_service.get_vendor_or_404(db, vendor_id))


@router.patch("/{vendor_id}", response_model=HardwareVendorPartnerOut)
def update_vendor(
    vendor_id: str, body: HardwareVendorPartnerUpdate, db: Session = Depends(get_db)
) -> HardwareVendorPartnerOut:
    return HardwareVendorPartnerOut.model_validate(vendor_service.update_vendor(db, vendor_id, body))


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: str, db: Session = Depends(get_db)) -> None:
    vendor_service.delete_vendor(db, vendor_id)


@router.put("/{vendor_id}/webhook", response_model=WebhookOut)
def configure_webhook(
    vendor_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)
) -> WebhookOut:
    return vendor_service.configure_webhook(db, vendor_id, body)


@router.get("/{vendor_id}/webhook", response_model=WebhookOut)
def get_webhook(vendor_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = vendor_service.get_webhook(db, vendor_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{vendor_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(vendor_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return vendor_service.rotate_api_key(db, vendor_id)


@router.get("/{vendor_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(vendor_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return vendor_service.list_api_keys(db, vendor_id)
