from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ml_alerts_webhooks import MlReadinessAlert, MlReadinessScoreHistory
from app.services import ml_capability_webhook_service
from app.services.crypto_util import new_id

SCORE_DROP_THRESHOLD = 5.0
BAND_RANK = {"GO_LIVE": 0, "PILOT": 1, "PLANNED": 2, "BLOCKED": 3}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def record_ml_score_and_check_alerts(
    db: Session,
    *,
    network_player_id: str,
    network_player_code: str,
    previous_score: float | None,
    previous_band: str | None,
    new_score: float,
    new_band: str,
) -> dict[str, int]:
    alerts_created = webhooks_sent = 0
    db.add(
        MlReadinessScoreHistory(
            id=new_id(),
            network_player_id=network_player_id,
            network_player_code=network_player_code,
            score_total=new_score,
            readiness_band=new_band,
            recorded_at=_utcnow(),
        )
    )
    if previous_score is not None:
        delta = round(previous_score - new_score, 2)
        worsened = BAND_RANK.get(new_band, 99) > BAND_RANK.get(previous_band or "", 0)
        if delta >= SCORE_DROP_THRESHOLD or worsened:
            severity = "CRITICAL" if worsened or delta >= 15 else "WARNING"
            alert = MlReadinessAlert(
                id=new_id(),
                network_player_id=network_player_id,
                network_player_code=network_player_code,
                alert_type="SCORE_DROP",
                severity=severity,
                previous_score=previous_score,
                new_score=new_score,
                score_delta=delta,
                previous_band=previous_band,
                new_band=new_band,
                status="OPEN",
            )
            db.add(alert)
            alerts_created += 1
            db.flush()
            webhooks_sent += ml_capability_webhook_service.dispatch_ml_player_event(
                db,
                network_player_id,
                ml_capability_webhook_service.EVENT_READINESS_SCORE_DROP,
                {
                    "network_player_code": network_player_code,
                    "alert_id": alert.id,
                    "previous_score": previous_score,
                    "new_score": new_score,
                    "score_delta": delta,
                },
            )
            alert.webhook_dispatched = webhooks_sent > 0
    return {"alerts_created": alerts_created, "webhooks_sent": webhooks_sent}


def list_ml_readiness_alerts(db: Session, open_only: bool = True) -> list[MlReadinessAlert]:
    q = db.query(MlReadinessAlert)
    if open_only:
        q = q.filter(MlReadinessAlert.status == "OPEN")
    return q.order_by(MlReadinessAlert.created_at.desc()).all()
