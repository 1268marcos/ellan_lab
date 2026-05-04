from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.locker import CompatibilityCheckIn, CompatibilityCheckOut
from app.services import partner_service

router = APIRouter(tags=["compatibility"])


@router.post("/partners/{partner_id}/check-compatibility", response_model=CompatibilityCheckOut)
def check_compatibility(
    partner_id: str,
    body: CompatibilityCheckIn,
    db: Session = Depends(get_db),
) -> CompatibilityCheckOut:
    if not partner_service.get_partner(db, partner_id):
        raise HTTPException(status_code=404, detail="partner not found")
    raw = partner_service.check_compatibility_stub(partner_id, body.partner_sku, body.locker_id)
    return CompatibilityCheckOut.model_validate(raw)
