from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/noc", tags=["NOC/SIMT"])


class IncidentAckIn(BaseModel):
    incident_id: str
    acknowledged_by: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/health")
async def noc_health():
    return {
        "status": "ok",
        "service": "noc-simt",
        "runtime": {"status": "ok"},
        "lifecycle": {"status": "unknown", "mode": "mvp-polling"},
        "generated_at": _now_iso(),
    }


@router.get("/simt/summary")
async def simt_summary():
    return {
        "status": "ok",
        "service": "noc-simt",
        "mode": "mvp-polling",
        "lockers": {
            "total": 1,
            "operational": 1,
            "degraded": 0,
            "offline": 0,
        },
        "incidents": {
            "open": 0,
            "acknowledged": 0,
            "critical": 0,
        },
        "generated_at": _now_iso(),
    }


@router.post("/incidents/ack")
async def acknowledge_incident(payload: IncidentAckIn):
    return {
        "status": "acknowledged",
        "incident_id": payload.incident_id,
        "acknowledged_by": payload.acknowledged_by,
        "acknowledged_at": _now_iso(),
    }
