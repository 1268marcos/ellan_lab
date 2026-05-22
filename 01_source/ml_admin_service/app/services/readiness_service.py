from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ml_ecosystem import MlMarketPresence, MlPlayerCapability
from app.models.ml_network import MlLockerNetworkPlayer, MlNetworkMlProfile
from app.models.ml_readiness import MlIntegrationReadinessSnapshot, MlOpsAuditLog
from app.models.partner import MlDataPartner
from app.services.crypto_util import new_id

BAND_GO_LIVE = "GO_LIVE"
BAND_PILOT = "PILOT"
BAND_PLANNED = "PLANNED"
BAND_BLOCKED = "BLOCKED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _append_audit(db: Session, event_type: str, summary: str, payload: dict | None = None) -> None:
    db.add(
        MlOpsAuditLog(
            id=new_id(),
            event_type=event_type,
            entity_type="NETWORK_PLAYER",
            summary=summary,
            payload_json=json.dumps(payload or {}),
            created_at=_utcnow(),
        )
    )


def _score_network_player(db: Session, player: MlLockerNetworkPlayer) -> dict:
    caps = (
        db.query(MlPlayerCapability)
        .filter(
            MlPlayerCapability.network_player_id == player.id,
            MlPlayerCapability.enabled.is_(True),
        )
        .all()
    )
    cap_count = len(caps)
    prod_caps = sum(1 for c in caps if c.production_ready)
    score_capabilities = min(35.0, cap_count * 7.0 + prod_caps * 3.0)

    partner = None
    if hasattr(MlDataPartner, "network_player_code"):
        partner = (
            db.query(MlDataPartner)
            .filter(MlDataPartner.network_player_code == player.code, MlDataPartner.active.is_(True))
            .first()
        )
    score_telemetry = 0.0
    blockers: list[str] = []
    if partner:
        score_telemetry = 25.0
    elif player.code.startswith("TELEMETRY"):
        score_telemetry = 15.0
    else:
        blockers.append("no_telemetry_partner")

    profiles = (
        db.query(MlNetworkMlProfile)
        .filter(MlNetworkMlProfile.network_player_id == player.id, MlNetworkMlProfile.active.is_(True))
        .count()
    )
    markets = (
        db.query(MlMarketPresence)
        .filter(MlMarketPresence.network_player_id == player.id, MlMarketPresence.active.is_(True))
        .count()
    )
    score_ml_ops = min(40.0, profiles * 12.0 + markets * 2.0)
    if profiles == 0:
        blockers.append("no_ml_profile")

    tier_bonus = {"TIER1": 10, "TIER2": 6, "REGIONAL": 2}.get(getattr(player, "global_tier", None) or "REGIONAL", 0)
    status_bonus = 5 if getattr(player, "integration_status", None) == "PILOT" else 0
    score_total = min(100.0, score_capabilities + score_telemetry + score_ml_ops + tier_bonus + status_bonus)

    if score_total >= 70 and cap_count >= 1 and profiles >= 1:
        band = BAND_GO_LIVE
    elif score_total >= 45:
        band = BAND_PILOT
    elif score_total >= 20:
        band = BAND_PLANNED
    else:
        band = BAND_BLOCKED

    return {
        "network_player_id": player.id,
        "network_player_code": player.code,
        "marketplace_channel_id": player.marketplace_channel_id,
        "score_total": round(score_total, 2),
        "score_capabilities": round(score_capabilities, 2),
        "score_telemetry": round(score_telemetry, 2),
        "score_ml_ops": round(score_ml_ops, 2),
        "readiness_band": band,
        "blockers": blockers,
        "factors": {
            "capability_count": cap_count,
            "production_capabilities": prod_caps,
            "ml_profiles": profiles,
            "market_presence": markets,
            "global_tier": getattr(player, "global_tier", None),
            "has_telemetry_partner": partner is not None,
        },
    }


def recompute_ml_readiness(db: Session) -> dict:
    players = db.query(MlLockerNetworkPlayer).filter(MlLockerNetworkPlayer.active.is_(True)).all()
    upserted = 0
    bands: dict[str, int] = {}
    from app.services import ml_readiness_alert_service

    alerts_created = webhooks_sent = 0
    for player in players:
        scored = _score_network_player(db, player)
        row = (
            db.query(MlIntegrationReadinessSnapshot)
            .filter(MlIntegrationReadinessSnapshot.network_player_id == player.id)
            .first()
        )
        prev_score = float(row.score_total) if row else None
        prev_band = row.readiness_band if row else None
        astats = ml_readiness_alert_service.record_ml_score_and_check_alerts(
            db,
            network_player_id=player.id,
            network_player_code=scored["network_player_code"],
            previous_score=prev_score,
            previous_band=prev_band,
            new_score=scored["score_total"],
            new_band=scored["readiness_band"],
        )
        alerts_created += astats["alerts_created"]
        webhooks_sent += astats["webhooks_sent"]
        payload = {
            "network_player_code": scored["network_player_code"],
            "marketplace_channel_id": scored["marketplace_channel_id"],
            "score_total": scored["score_total"],
            "score_capabilities": scored["score_capabilities"],
            "score_telemetry": scored["score_telemetry"],
            "score_ml_ops": scored["score_ml_ops"],
            "readiness_band": scored["readiness_band"],
            "blockers_json": json.dumps(scored["blockers"]),
            "factors_json": json.dumps(scored["factors"]),
            "computed_at": _utcnow(),
        }
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(MlIntegrationReadinessSnapshot(id=new_id(), network_player_id=player.id, **payload))
        upserted += 1
        bands[scored["readiness_band"]] = bands.get(scored["readiness_band"], 0) + 1

    _append_audit(db, "ML_READINESS_RECOMPUTE", f"Prontidao ML para {upserted} redes", {"bands": bands, "alerts": alerts_created})
    db.commit()
    return {"upserted": upserted, "bands": bands, "alerts_created": alerts_created, "webhooks_sent": webhooks_sent}


def list_ml_readiness(db: Session, band: str | None = None, limit: int = 200) -> list[dict]:
    q = db.query(MlIntegrationReadinessSnapshot)
    if band:
        q = q.filter(MlIntegrationReadinessSnapshot.readiness_band == band.upper())
    rows = q.order_by(MlIntegrationReadinessSnapshot.score_total.desc()).limit(limit).all()
    out = []
    for r in rows:
        try:
            blockers = json.loads(r.blockers_json or "[]")
        except json.JSONDecodeError:
            blockers = []
        try:
            factors = json.loads(r.factors_json or "{}")
        except json.JSONDecodeError:
            factors = {}
        out.append(
            {
                "id": r.id,
                "network_player_id": r.network_player_id,
                "network_player_code": r.network_player_code,
                "marketplace_channel_id": r.marketplace_channel_id,
                "score_total": float(r.score_total),
                "score_capabilities": float(r.score_capabilities),
                "score_telemetry": float(r.score_telemetry),
                "score_ml_ops": float(r.score_ml_ops),
                "readiness_band": r.readiness_band,
                "blockers": blockers,
                "factors": factors,
                "computed_at": r.computed_at,
            }
        )
    return out


def ml_readiness_hub_summary(db: Session) -> dict:
    rows = db.query(MlIntegrationReadinessSnapshot).all()
    bands = {BAND_GO_LIVE: 0, BAND_PILOT: 0, BAND_PLANNED: 0, BAND_BLOCKED: 0}
    total = 0.0
    for r in rows:
        bands[r.readiness_band] = bands.get(r.readiness_band, 0) + 1
        total += float(r.score_total or 0)
    from app.models.ml_alerts_webhooks import MlReadinessAlert

    audits = db.query(MlOpsAuditLog).count()
    open_alerts = db.query(MlReadinessAlert).filter(MlReadinessAlert.status == "OPEN").count()
    return {
        "readiness_rows": len(rows),
        "avg_score": round(total / len(rows), 2) if rows else 0.0,
        "bands": bands,
        "audit_log_rows": audits,
        "open_readiness_alerts": open_alerts,
    }


def readiness_dashboard_counts(db: Session) -> dict:
    summary = ml_readiness_hub_summary(db)
    return {
        "ml_readiness_rows": summary["readiness_rows"],
        "ml_readiness_go_live": summary["bands"].get(BAND_GO_LIVE, 0),
        "ml_readiness_avg_score": summary["avg_score"],
        "ml_readiness_alerts_open": summary.get("open_readiness_alerts", 0),
    }
