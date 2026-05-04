from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    PartnerApiKeyRotateIn,
    PartnerApiKeyRotateOut,
    PartnerCreateIn,
    PartnerOut,
    PartnerUpdateIn,
    PartnerWebhookPatchIn,
)
from services import partner_service

router = APIRouter(prefix="/partners", tags=["partners"])


@router.post("", response_model=PartnerOut, status_code=201)
def create_partner(payload: PartnerCreateIn, db: Session = Depends(get_db)) -> PartnerOut:
    row = partner_service.create_partner(db, payload)
    return PartnerOut.model_validate(row)


@router.get("", response_model=list[PartnerOut])
def list_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[PartnerOut]:
    rows = partner_service.list_partners(db, skip=skip, limit=limit)
    return [PartnerOut.model_validate(r) for r in rows]


@router.get("/{partner_id}", response_model=PartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> PartnerOut:
    row = partner_service.get_partner(db, partner_id)
    return PartnerOut.model_validate(row)


@router.patch("/{partner_id}", response_model=PartnerOut)
def update_partner(
    partner_id: str, payload: PartnerUpdateIn, db: Session = Depends(get_db)
) -> PartnerOut:
    row = partner_service.update_partner(db, partner_id, payload)
    return PartnerOut.model_validate(row)


@router.delete("/{partner_id}", status_code=204)
def delete_partner(partner_id: str, db: Session = Depends(get_db)) -> None:
    partner_service.delete_partner(db, partner_id)


@router.patch("/{partner_id}/webhook", response_model=PartnerOut)
def patch_webhook(
    partner_id: str, payload: PartnerWebhookPatchIn, db: Session = Depends(get_db)
) -> PartnerOut:
    row = partner_service.update_webhook(db, partner_id, payload)
    return PartnerOut.model_validate(row)


@router.post("/{partner_id}/api-keys/rotate", response_model=PartnerApiKeyRotateOut)
def rotate_api_key(
    partner_id: str,
    payload: PartnerApiKeyRotateIn | None = Body(default=None),
    db: Session = Depends(get_db),
) -> PartnerApiKeyRotateOut:
    body = payload if payload is not None else PartnerApiKeyRotateIn()
    raw, row = partner_service.rotate_api_key(db, partner_id, body.label)
    return PartnerApiKeyRotateOut(
        id=row.id,
        key_prefix=row.key_prefix,
        api_key=raw,
        partner_id=row.partner_id,
    )
