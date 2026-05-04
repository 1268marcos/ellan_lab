from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.locker import EligibleLockersResponse
from app.services import partner_service

router = APIRouter(tags=["lockers"])


@router.get("/partners/{partner_id}/eligible-lockers", response_model=EligibleLockersResponse)
def eligible_lockers(
    partner_id: str,
    product_sku: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> EligibleLockersResponse:
    if not partner_service.get_partner(db, partner_id):
        raise HTTPException(status_code=404, detail="partner not found")
    raw = partner_service.eligible_lockers_for_partner(partner_id, product_sku)
    return EligibleLockersResponse.model_validate(raw)
