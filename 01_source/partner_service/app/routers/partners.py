from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner import ApiKeyRotateResponse, PartnerCreate, PartnerCreateResponse, PartnerOut
from app.services import partner_service

router = APIRouter(tags=["partners"])


@router.post("/partners", response_model=PartnerCreateResponse, status_code=status.HTTP_201_CREATED)
def create_partner(body: PartnerCreate, db: Session = Depends(get_db)) -> PartnerCreateResponse:
    partner, raw_key = partner_service.create_partner(db, body)
    out = partner_service.partner_to_out(partner)
    return PartnerCreateResponse(**out.model_dump(), api_key=raw_key)


@router.get("/partners/{partner_id}", response_model=PartnerOut)
async def read_partner(partner_id: str, db: Session = Depends(get_db)) -> PartnerOut:
    p = partner_service.get_partner(db, partner_id)
    if not p:
        raise HTTPException(status_code=404, detail="partner not found")
    payload = partner_service.partner_to_public_dict(p)
    partner_service.schedule_shadow_compare(partner_id, payload)
    return partner_service.partner_to_out(p)


@router.put("/partners/{partner_id}/apikey/rotate", response_model=ApiKeyRotateResponse)
def rotate_api_key(partner_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateResponse:
    rotated = partner_service.rotate_api_key(db, partner_id)
    if not rotated:
        raise HTTPException(status_code=404, detail="partner not found")
    raw, prefix = rotated
    return ApiKeyRotateResponse(api_key=raw, key_prefix=prefix)
