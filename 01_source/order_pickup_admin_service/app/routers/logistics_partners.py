from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner import (
    LogisticsPartnerCreateIn,
    LogisticsPartnerListOut,
    LogisticsPartnerOut,
    LogisticsPartnerUpdateIn,
)
from app.services import partner_service

router = APIRouter(prefix="/logistics-partners", tags=["logistics-partners"])


@router.get("", response_model=LogisticsPartnerListOut)
def list_partners(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> LogisticsPartnerListOut:
    partners = partner_service.list_logistics(db, active_only=active_only)
    return LogisticsPartnerListOut(partners=partners, total=len(partners))


@router.post("", response_model=LogisticsPartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(body: LogisticsPartnerCreateIn, db: Session = Depends(get_db)) -> LogisticsPartnerOut:
    return partner_service.create_logistics(db, body)


@router.get("/{partner_id}", response_model=LogisticsPartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> LogisticsPartnerOut:
    return LogisticsPartnerOut.model_validate(partner_service.get_logistics_or_404(db, partner_id))


@router.patch("/{partner_id}", response_model=LogisticsPartnerOut)
def update_partner(
    partner_id: str,
    body: LogisticsPartnerUpdateIn,
    db: Session = Depends(get_db),
) -> LogisticsPartnerOut:
    return partner_service.update_logistics(db, partner_id, body)


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: str, db: Session = Depends(get_db)) -> None:
    partner_service.delete_logistics(db, partner_id)
