from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ml_readiness import MlOpsAuditLog
from pydantic import BaseModel, Field

from app.schemas.ml_readiness import MlReadinessHubOut, MlReadinessListOut, MlReadinessOut
from app.services import ml_capability_webhook_service, readiness_service
from app.services import ml_readiness_alert_service

router = APIRouter(tags=["ml-readiness"])


@router.get("/ml-readiness-hub/summary", response_model=MlReadinessHubOut)
def ml_readiness_hub(db: Session = Depends(get_db)) -> MlReadinessHubOut:
    return MlReadinessHubOut(**readiness_service.ml_readiness_hub_summary(db))


@router.post("/ml-integration-readiness/recompute")
def recompute_ml_readiness(db: Session = Depends(get_db)) -> dict:
    return readiness_service.recompute_ml_readiness(db)


@router.get("/ml-integration-readiness", response_model=MlReadinessListOut)
def list_ml_readiness(
    band: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> MlReadinessListOut:
    items = [MlReadinessOut.model_validate(x) for x in readiness_service.list_ml_readiness(db, band=band, limit=limit)]
    return MlReadinessListOut(items=items, total=len(items))


class MlCapabilityWebhookIn(BaseModel):
    network_player_id: str
    capability_code: str
    url: str
    secret: str | None = None
    events: list[str] | None = None


@router.get("/ml-readiness-alerts")
def list_ml_readiness_alerts(open_only: bool = Query(True), db: Session = Depends(get_db)) -> dict:
    rows = ml_readiness_alert_service.list_ml_readiness_alerts(db, open_only=open_only)
    return {
        "items": [
            {
                "id": r.id,
                "network_player_code": r.network_player_code,
                "alert_type": r.alert_type,
                "severity": r.severity,
                "score_delta": float(r.score_delta),
                "previous_score": float(r.previous_score) if r.previous_score is not None else None,
                "new_score": float(r.new_score),
                "status": r.status,
                "webhook_dispatched": r.webhook_dispatched,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/ml-capability-webhooks")
def list_ml_capability_webhooks(
    network_player_id: str | None = Query(None), db: Session = Depends(get_db)
) -> dict:
    rows = ml_capability_webhook_service.list_ml_capability_webhooks(db, network_player_id)
    return {
        "items": [
            {
                "id": r.id,
                "network_player_code": r.network_player_code,
                "capability_code": r.capability_code,
                "url": r.url,
                "active": r.active,
                "last_http_status": r.last_http_status,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.put("/ml-capability-webhooks")
def upsert_ml_capability_webhook(body: MlCapabilityWebhookIn, db: Session = Depends(get_db)) -> dict:
    row = ml_capability_webhook_service.configure_ml_capability_webhook(
        db,
        network_player_id=body.network_player_id,
        capability_code=body.capability_code,
        url=body.url,
        secret=body.secret,
        events=body.events,
    )
    return {"id": row.id, "network_player_code": row.network_player_code, "capability_code": row.capability_code}


@router.get("/ml-ops-audit-log")
def list_ml_ops_audit(limit: int = Query(40, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    rows = db.query(MlOpsAuditLog).order_by(MlOpsAuditLog.created_at.desc()).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "entity_type": r.entity_type,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": len(rows),
    }
