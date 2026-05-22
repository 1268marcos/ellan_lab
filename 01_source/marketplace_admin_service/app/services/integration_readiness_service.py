from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.marketplace_extended import MarketplaceChannelCapability, MarketplaceChannelPartner
from app.models.marketplace_integration import (
    MarketplaceIntegrationIncident,
    MarketplaceIntegrationReadiness,
    MarketplaceSyncAuditLog,
)
from app.services.crypto_util import new_id

BAND_GO_LIVE = "GO_LIVE"
BAND_PILOT = "PILOT"
BAND_PLANNED = "PLANNED"
BAND_BLOCKED = "BLOCKED"

MODE_SCORES = {
    "LOCKER_NETWORK_API": 12,
    "BIDIRECTIONAL": 10,
    "AGGREGATOR": 8,
    "DIRECT_API": 6,
    "WEBHOOK_INBOUND": 4,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def append_audit(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    summary: str,
    entity_id: str | None = None,
    actor_id: str | None = None,
    payload: dict | None = None,
) -> None:
    db.add(
        MarketplaceSyncAuditLog(
            id=new_id(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            summary=summary,
            payload_json=json.dumps(payload or {}),
            created_at=_utcnow(),
        )
    )


def _score_partner(db: Session, partner: MarketplaceChannelPartner) -> dict:
    caps = (
        db.query(MarketplaceChannelCapability)
        .filter(
            MarketplaceChannelCapability.channel_partner_id == partner.id,
            MarketplaceChannelCapability.enabled.is_(True),
        )
        .all()
    )
    cap_count = len(caps)
    score_capabilities = min(40.0, cap_count * 8.0)

    blockers: list[str] = []
    score_api = 15.0 if partner.api_docs_url else 0.0
    if not partner.api_docs_url:
        blockers.append("missing_api_docs")

    score_ops = 0.0
    if partner.locker_operator_ref:
        score_ops += 10.0
    else:
        if partner.supports_lockers or partner.parent_group in ("LOCKER_NETWORK", "CARRIER_LAST_MILE"):
            blockers.append("missing_locker_operator_ref")

    score_ops += float(MODE_SCORES.get(partner.integration_mode or "", 3))
    try:
        regions = json.loads(partner.regions_json or "[]")
        if isinstance(regions, list):
            score_ops += min(15.0, len(regions) * 3.0)
    except json.JSONDecodeError:
        pass
    if partner.supports_lockers:
        score_ops += 5.0

    score_ops = min(45.0, score_ops)
    score_total = min(100.0, score_capabilities + score_api + score_ops)

    if partner.parent_group == "LOGISTICS_PLATFORM" and cap_count == 0:
        blockers.append("aggregator_without_capabilities")
    if cap_count == 0 and partner.parent_group in ("MARKETPLACE", "LOCKER_NETWORK"):
        blockers.append("no_capabilities_defined")

    if score_total >= 75 and cap_count >= 2 and not blockers:
        band = BAND_GO_LIVE
    elif score_total >= 45 and cap_count >= 1:
        band = BAND_PILOT
    elif score_total >= 20:
        band = BAND_PLANNED
    else:
        band = BAND_BLOCKED

    if blockers and band == BAND_GO_LIVE:
        band = BAND_PILOT

    return {
        "channel_partner_id": partner.id,
        "partner_code": partner.code,
        "score_total": round(score_total, 2),
        "score_capabilities": round(score_capabilities, 2),
        "score_api": round(score_api, 2),
        "score_operations": round(score_ops, 2),
        "readiness_band": band,
        "blockers": blockers,
        "ml_network_code": partner.code,
    }


def recompute_all_readiness(db: Session, *, actor_id: str | None = None) -> dict[str, int]:
    partners = db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.active.is_(True)).all()
    upserted = 0
    bands: dict[str, int] = {}
    from app.services import readiness_alert_service

    alerts_created = webhooks_sent = 0
    for partner in partners:
        scored = _score_partner(db, partner)
        row = db.get(MarketplaceIntegrationReadiness, partner.id)
        prev_score = float(row.score_total) if row else None
        prev_band = row.readiness_band if row else None
        alert_stats = readiness_alert_service.record_score_and_check_alerts(
            db,
            channel_partner_id=partner.id,
            partner_code=scored["partner_code"],
            previous_score=prev_score,
            previous_band=prev_band,
            new_score=scored["score_total"],
            new_band=scored["readiness_band"],
        )
        alerts_created += alert_stats["alerts_created"]
        webhooks_sent += alert_stats["webhooks_sent"]
        payload = {
            "partner_code": scored["partner_code"],
            "score_total": scored["score_total"],
            "score_capabilities": scored["score_capabilities"],
            "score_api": scored["score_api"],
            "score_operations": scored["score_operations"],
            "readiness_band": scored["readiness_band"],
            "blockers_json": json.dumps(scored["blockers"]),
            "ml_network_code": scored["ml_network_code"],
            "computed_at": _utcnow(),
        }
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(MarketplaceIntegrationReadiness(channel_partner_id=partner.id, **payload))
        upserted += 1
        bands[scored["readiness_band"]] = bands.get(scored["readiness_band"], 0) + 1

    append_audit(
        db,
        event_type="READINESS_RECOMPUTE",
        entity_type="CHANNEL_PARTNER",
        summary=f"Prontidao recalculada para {upserted} players",
        actor_id=actor_id,
        payload={"bands": bands, "total": upserted, "alerts_created": alerts_created},
    )
    db.commit()
    return {"upserted": upserted, "bands": bands, "alerts_created": alerts_created, "webhooks_sent": webhooks_sent}


def list_readiness(db: Session, band: str | None = None, limit: int = 200) -> list[MarketplaceIntegrationReadiness]:
    q = db.query(MarketplaceIntegrationReadiness)
    if band:
        q = q.filter(MarketplaceIntegrationReadiness.readiness_band == band.upper())
    return q.order_by(MarketplaceIntegrationReadiness.score_total.desc()).limit(limit).all()


def list_incidents(db: Session, *, open_only: bool = True) -> list[MarketplaceIntegrationIncident]:
    q = db.query(MarketplaceIntegrationIncident)
    if open_only:
        q = q.filter(MarketplaceIntegrationIncident.status == "OPEN")
    return q.order_by(MarketplaceIntegrationIncident.opened_at.desc()).all()


def seed_demo_incidents(db: Session) -> int:
    demos = [
        ("mcp-inpost", "INPOST", "WARNING", "API_DEGRADED", "Latencia elevada API ShipX (EU)", "OPEN"),
        ("mcp-correios", "CORREIOS", "CRITICAL", "CERT_EXPIRY", "Certificado mTLS proximo do vencimento", "OPEN"),
        ("mcp-meli", "MERCADOLIVRE", "INFO", "RATE_LIMIT", "Quota OAuth seller temporariamente reduzida", "OPEN"),
    ]
    n = 0
    for pid, code, sev, itype, title, status in demos:
        if db.query(MarketplaceIntegrationIncident).filter(MarketplaceIntegrationIncident.title == title).first():
            continue
        db.add(
            MarketplaceIntegrationIncident(
                id=new_id(),
                channel_partner_id=pid,
                partner_code=code,
                severity=sev,
                incident_type=itype,
                title=title,
                status=status,
                details_json=json.dumps({"source": "seed", "region": "BR" if code in ("CORREIOS", "MERCADOLIVRE") else "EU"}),
            )
        )
        n += 1
    return n


def hub_summary(db: Session) -> dict:
    rows = db.query(MarketplaceIntegrationReadiness).all()
    bands = {BAND_GO_LIVE: 0, BAND_PILOT: 0, BAND_PLANNED: 0, BAND_BLOCKED: 0}
    total_score = 0.0
    for r in rows:
        bands[r.readiness_band] = bands.get(r.readiness_band, 0) + 1
        total_score += float(r.score_total or 0)
    avg = round(total_score / len(rows), 2) if rows else 0.0
    open_incidents = (
        db.query(MarketplaceIntegrationIncident).filter(MarketplaceIntegrationIncident.status == "OPEN").count()
    )
    top_go_live = (
        db.query(MarketplaceIntegrationReadiness)
        .filter(MarketplaceIntegrationReadiness.readiness_band == BAND_GO_LIVE)
        .order_by(MarketplaceIntegrationReadiness.score_total.desc())
        .limit(8)
        .all()
    )
    critical_blockers = 0
    for r in rows:
        try:
            b = json.loads(r.blockers_json or "[]")
            if b:
                critical_blockers += 1
        except json.JSONDecodeError:
            pass
    from app.models.marketplace_alerts_webhooks import MarketplaceReadinessAlert

    open_alerts = (
        db.query(MarketplaceReadinessAlert).filter(MarketplaceReadinessAlert.status == "OPEN").count()
    )
    return {
        "readiness_rows": len(rows),
        "avg_score": avg,
        "bands": bands,
        "open_incidents": open_incidents,
        "open_readiness_alerts": open_alerts,
        "partners_with_blockers": critical_blockers,
        "top_go_live": [
            {
                "partner_code": t.partner_code,
                "score_total": float(t.score_total),
                "ml_network_code": t.ml_network_code,
            }
            for t in top_go_live
        ],
    }
