"""GET /ops/lockers/{locker_id}/occupancy-forecast"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app import db
from app.middleware.partner_scope import PartnerLockerScope, get_partner_lockers
from app.ml_demand.predict_occupancy import predict_occupancy_hours

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ops/lockers", tags=["ops-occupancy-forecast"])


@router.get("/{locker_id}/occupancy-forecast")
def get_occupancy_forecast(
    locker_id: str,
    scope: PartnerLockerScope = Depends(get_partner_lockers),
    hours: int = Query(24, ge=1, le=24),
) -> dict:
    lid = locker_id.strip()
    scope.raise_if_locker_forbidden(lid)
    row = db.fetch_one("SELECT id FROM lockers WHERE id = %s LIMIT 1", (lid,))
    if not row:
        raise HTTPException(404, "locker not found")
    try:
        return predict_occupancy_hours(lid, hours=hours)
    except Exception as exc:
        logger.exception("occupancy-forecast failed")
        raise HTTPException(500, str(exc)) from exc
