from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner import (
    EcommercePartnerCreateIn,
    EcommercePartnerListOut,
    EcommercePartnerOut,
    EcommercePartnerUpdateIn,
)
from app.services import partner_service

router = APIRouter(prefix="/ecommerce-partners", tags=["ecommerce-partners"])


@router.get("", response_model=EcommercePartnerListOut)
def list_partners(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> EcommercePartnerListOut:
    partners = partner_service.list_ecommerce(db, active_only=active_only)
    return EcommercePartnerListOut(partners=partners, total=len(partners))


@router.post("", response_model=EcommercePartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: EcommercePartnerCreateIn, db: Session = Depends(get_db)) -> EcommercePartnerOut:
    return partner_service.create_ecommerce(db, body)


@router.get("/{partner_id}", response_model=EcommercePartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> EcommercePartnerOut:
    return EcommercePartnerOut.model_validate(partner_service.get_ecommerce_or_404(db, partner_id))


@router.patch("/{partner_id}", response_model=EcommercePartnerOut)
def update_partner(
    partner_id: str,
    body: EcommercePartnerUpdateIn,
    db: Session = Depends(get_db),
) -> EcommercePartnerOut:
    return partner_service.update_ecommerce(db, partner_id, body)


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: str, db: Session = Depends(get_db)) -> None:
    partner_service.delete_ecommerce(db, partner_id)
