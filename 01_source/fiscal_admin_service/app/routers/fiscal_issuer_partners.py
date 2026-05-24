from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.fiscal import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    IssuerIn,
    IssuerListOut,
    IssuerOut,
    IssuerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services import issuer_service

router = APIRouter(prefix="/fiscal-issuer-partners", tags=["fiscal-issuer-partners"])


@router.get("", response_model=IssuerListOut)
def list_issuers(active_only: bool = Query(False), db: Session = Depends(get_db)) -> IssuerListOut:
    rows = issuer_service.list_issuers(db, active_only=active_only)
    out = [IssuerOut.model_validate(r) for r in rows]
    return IssuerListOut(issuers=out, total=len(out))


@router.post("", response_model=IssuerOut, status_code=status.HTTP_201_CREATED)
def create_issuer(body: IssuerIn, db: Session = Depends(get_db)) -> IssuerOut:
    return IssuerOut.model_validate(issuer_service.create_issuer(db, body))


@router.get("/{issuer_id}", response_model=IssuerOut)
def get_issuer(issuer_id: str, db: Session = Depends(get_db)) -> IssuerOut:
    return IssuerOut.model_validate(issuer_service.get_issuer_or_404(db, issuer_id))


@router.patch("/{issuer_id}", response_model=IssuerOut)
def update_issuer(issuer_id: str, body: IssuerUpdate, db: Session = Depends(get_db)) -> IssuerOut:
    return IssuerOut.model_validate(issuer_service.update_issuer(db, issuer_id, body))


@router.delete("/{issuer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issuer(issuer_id: str, db: Session = Depends(get_db)) -> None:
    issuer_service.delete_issuer(db, issuer_id)


@router.put("/{issuer_id}/webhook", response_model=WebhookOut)
def configure_webhook(issuer_id: str, body: WebhookConfigureIn, db: Session = Depends(get_db)) -> WebhookOut:
    return issuer_service.configure_webhook(db, issuer_id, body)


@router.get("/{issuer_id}/webhook", response_model=WebhookOut)
def get_webhook(issuer_id: str, db: Session = Depends(get_db)) -> WebhookOut:
    row = issuer_service.get_webhook(db, issuer_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")
    return row


@router.post("/{issuer_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(issuer_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return issuer_service.rotate_api_key(db, issuer_id)


@router.get("/{issuer_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(issuer_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return issuer_service.list_api_keys(db, issuer_id)
