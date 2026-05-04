from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import logistics_service, sla_service

router = APIRouter(prefix="/api/v1", tags=["delivery"])


class TrackBody(BaseModel):
    tracking: str
    manifest_id: str | None = None
    eta: datetime | None = None
    signature: str | None = None


@router.post("/delivery/track", status_code=201)
def post_track(body: TrackBody, db: Session = Depends(get_db)) -> dict[str, Any]:
    d = logistics_service.track_delivery(
        db,
        body.tracking,
        manifest_id=body.manifest_id,
        eta=body.eta,
        signature=body.signature,
    )
    return {
        "id": d.id,
        "tracking": d.tracking,
        "manifest_id": d.manifest_id,
        "eta": d.eta.isoformat() if d.eta else None,
        "signature": d.signature,
    }


@router.get("/delivery/{delivery_id}/eta")
def get_eta(delivery_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    d = logistics_service.get_delivery(db, delivery_id)
    if not d:
        raise HTTPException(status_code=404, detail="delivery_not_found")
    return {"id": d.id, "eta": d.eta.isoformat() if d.eta else None}


@router.get("/sla/compliance")
def get_sla_compliance() -> dict[str, Any]:
    return sla_service.fetch_compliance()
