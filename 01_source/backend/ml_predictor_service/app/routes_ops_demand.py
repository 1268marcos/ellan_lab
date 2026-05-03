"""GET /ops/lockers/{locker_id}/occupancy-forecast"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app import db
from app.ml_demand.predict_occupancy import predict_occupancy_hours

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ops/lockers", tags=["ops-occupancy-forecast"])


@router.get("/{locker_id}/occupancy-forecast")
def get_occupancy_forecast(locker_id: str, hours: int = Query(24, ge=1, le=24)) -> dict:
    lid = locker_id.strip()
    row = db.fetch_one("SELECT id FROM lockers WHERE id = %s LIMIT 1", (lid,))
    if not row:
        raise HTTPException(404, "locker not found")
    try:
        return predict_occupancy_hours(lid, hours=hours)
    except Exception as exc:
        logger.exception("occupancy-forecast failed")
        raise HTTPException(500, str(exc)) from exc
