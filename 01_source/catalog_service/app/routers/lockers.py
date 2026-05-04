from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import compatibility_service

router = APIRouter(tags=["lockers"])


@router.get("/partners/{partner_id}/eligible-lockers")
def eligible_lockers(
    partner_id: str,
    product_sku: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return compatibility_service.eligible_lockers(db, partner_id, product_sku)
