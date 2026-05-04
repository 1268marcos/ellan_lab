from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import logistics_service

router = APIRouter(prefix="/api/v1", tags=["manifest"])


class ManifestCreate(BaseModel):
    shipments: list[dict[str, Any]] = Field(default_factory=list)
    locker_id: str
    status: str = "draft"


@router.post("/manifest", status_code=status.HTTP_201_CREATED)
def post_manifest(body: ManifestCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    m = logistics_service.create_manifest(db, body.shipments, body.locker_id, body.status)
    return {
        "id": m.id,
        "locker_id": m.locker_id,
        "status": m.status,
        "shipments": json.loads(m.shipments),
    }


@router.get("/manifest/{manifest_id}")
def get_manifest(manifest_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    m = logistics_service.get_manifest(db, manifest_id)
    if not m:
        raise HTTPException(status_code=404, detail="manifest_not_found")
    return {
        "id": m.id,
        "locker_id": m.locker_id,
        "status": m.status,
        "shipments": json.loads(m.shipments),
    }
