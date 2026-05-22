from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base
from app.data.global_ops_seed import CERTIFICATIONS_BY_PLAYER, CORRIDORS, CORRIDOR_SLA

_CROSS_SCHEMA_TABLES = frozenset(
    {"marketplace_player_certifications", "partner_player_certifications", "marketplace_capability_webhooks"}
)
from app.models.partner_capability_webhook import PartnerCapabilityWebhook
from app.models.partner_ecosystem import PartnerEcosystemPlayer
from app.models.partner_ecosystem_professional import PartnerPlayerCapability, PartnerPlayerRelation
from app.models.partner_global_ops import (
    PartnerCorridorSla,
    PartnerEcosystemReadiness,
    PartnerGlobalCorridor,
    PartnerPlayerCertification,
    PartnerRelationHealth,
)
from app.services.crypto_util import new_id

BAND_GO_LIVE = "GO_LIVE"
BAND_PILOT = "PILOT"
BAND_PLANNED = "PLANNED"
BAND_BLOCKED = "BLOCKED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _player_map(db: Session) -> dict[str, PartnerEcosystemPlayer]:
    rows = db.query(PartnerEcosystemPlayer).all()
    return {r.code.upper(): r for r in rows}


def seed_global_ops(db: Session) -> dict[str, int]:
    players = _player_map(db)
    certs = 0
    for code, items in CERTIFICATIONS_BY_PLAYER.items():
        player = players.get(code.upper())
        if not player:
            continue
        for cert_type, issuer, status, years in items:
            issued = date.today() - timedelta(days=180)
            expires = date.today() + timedelta(days=365 * years)
            existing = (
                db.query(PartnerPlayerCertification)
                .filter(
                    PartnerPlayerCertification.ecosystem_player_id == player.id,
                    PartnerPlayerCertification.certification_type == cert_type,
                )
                .first()
            )
            if existing:
                existing.status = status
                existing.issuer = issuer
                existing.issued_at = issued
                existing.expires_at = expires
            else:
                db.add(
                    PartnerPlayerCertification(
                        id=new_id(),
                        ecosystem_player_id=player.id,
                        player_code=player.code,
                        certification_type=cert_type,
                        status=status,
                        issuer=issuer,
                        issued_at=issued,
                        expires_at=expires,
                        evidence_url=f"https://compliance.example/{player.code.lower()}/{cert_type.lower()}",
                    )
                )
            certs += 1

    corridors = 0
    for spec in CORRIDORS:
        primary = players.get(spec["primary"].upper())
        if not primary:
            continue
        fallback = players.get(spec["fallback"].upper()) if spec.get("fallback") else None
        row = db.query(PartnerGlobalCorridor).filter(PartnerGlobalCorridor.corridor_code == spec["corridor_code"]).first()
        payload = dict(
            name=spec["name"],
            origin_country=spec["origin_country"],
            dest_country=spec["dest_country"],
            primary_player_id=primary.id,
            primary_player_code=primary.code,
            fallback_player_id=fallback.id if fallback else None,
            fallback_player_code=fallback.code if fallback else None,
            handoff_type=spec["handoff_type"],
            service_level=spec["service_level"],
            transit_days_min=spec["transit_days_min"],
            transit_days_max=spec["transit_days_max"],
            supports_returns=spec.get("supports_returns", False),
            active=True,
            priority=spec.get("priority", 100),
            notes=spec.get("notes"),
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(PartnerGlobalCorridor(id=new_id(), corridor_code=spec["corridor_code"], **payload))
        corridors += 1

    db.flush()
    sla_rows = seed_corridor_sla(db)
    cert_mirror = mirror_certifications_bidirectional(db)
    readiness = recompute_ecosystem_readiness(db)
    relation_health = recompute_relation_health(db)
    db.commit()
    return {
        "certifications": certs,
        "corridors": corridors,
        "corridor_sla": sla_rows,
        "certifications_mirror": cert_mirror,
        "readiness_rows": readiness["updated"],
        "relation_health_rows": relation_health["updated"],
    }


def _has_table(db: Session, name: str) -> bool:
    if name in Base.metadata.tables:
        return True
    if name not in _CROSS_SCHEMA_TABLES:
        return False
    try:
        with db.begin_nested():
            db.execute(text(f"SELECT 1 FROM {name} LIMIT 0"))
        return True
    except Exception:
        return False


def seed_corridor_sla(db: Session) -> int:
    count = 0
    corridors = db.query(PartnerGlobalCorridor).filter(PartnerGlobalCorridor.active.is_(True)).all()
    for c in corridors:
        spec = CORRIDOR_SLA.get(c.corridor_code, {})
        max_hours = spec.get("max_transit_hours") or max(c.transit_days_max * 24, 24)
        row = db.query(PartnerCorridorSla).filter(PartnerCorridorSla.corridor_id == c.id).first()
        payload = dict(
            corridor_code=c.corridor_code,
            uptime_target_pct=spec.get("uptime_target_pct", 99.5),
            on_time_delivery_pct=spec.get("on_time_delivery_pct", 95.0),
            max_transit_hours=max_hours,
            webhook_p95_latency_ms=spec.get("webhook_p95_latency_ms", 2000),
            compliance_status=spec.get("compliance_status", "COMPLIANT"),
            measured_at=_utcnow(),
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(PartnerCorridorSla(id=new_id(), corridor_id=c.id, **payload))
        count += 1
    return count


def mirror_certifications_from_marketplace(db: Session) -> dict[str, int]:
    if not _has_table(db, "marketplace_player_certifications"):
        return {"created": 0, "updated": 0, "skipped_no_table": 1}
    rows = db.execute(
        text(
            """
            SELECT id, channel_partner_id, partner_code, certification_type, status, issuer,
                   issued_at, expires_at, evidence_url, scope_notes
            FROM marketplace_player_certifications
            """
        )
    ).mappings().all()
    created = updated = 0
    for m in rows:
        player = (
            db.query(PartnerEcosystemPlayer)
            .filter(PartnerEcosystemPlayer.marketplace_channel_id == m["channel_partner_id"])
            .first()
        )
        if not player:
            player = (
                db.query(PartnerEcosystemPlayer)
                .filter(PartnerEcosystemPlayer.code == str(m["partner_code"]).upper())
                .first()
            )
        if not player:
            continue
        existing = (
            db.query(PartnerPlayerCertification)
            .filter(
                PartnerPlayerCertification.ecosystem_player_id == player.id,
                PartnerPlayerCertification.certification_type == m["certification_type"],
            )
            .first()
        )
        if existing:
            existing.status = m["status"]
            existing.issuer = m["issuer"]
            existing.issued_at = m["issued_at"]
            existing.expires_at = m["expires_at"]
            existing.evidence_url = m["evidence_url"]
            existing.scope_notes = m["scope_notes"]
            existing.marketplace_certification_id = m["id"]
            existing.source = "MARKETPLACE_MIRROR"
            updated += 1
        else:
            db.add(
                PartnerPlayerCertification(
                    id=new_id(),
                    ecosystem_player_id=player.id,
                    player_code=player.code,
                    certification_type=m["certification_type"],
                    status=m["status"],
                    issuer=m["issuer"],
                    issued_at=m["issued_at"],
                    expires_at=m["expires_at"],
                    evidence_url=m["evidence_url"],
                    scope_notes=m["scope_notes"],
                    marketplace_certification_id=m["id"],
                    source="MARKETPLACE_MIRROR",
                )
            )
            created += 1
    return {"created": created, "updated": updated}


def mirror_certifications_to_marketplace(db: Session) -> dict[str, int]:
    if not _has_table(db, "marketplace_player_certifications"):
        return {"created": 0, "updated": 0, "skipped_no_table": 1}
    created = updated = 0
    certs = (
        db.query(PartnerPlayerCertification, PartnerEcosystemPlayer)
        .join(PartnerEcosystemPlayer, PartnerPlayerCertification.ecosystem_player_id == PartnerEcosystemPlayer.id)
        .filter(PartnerEcosystemPlayer.marketplace_channel_id.isnot(None))
        .all()
    )
    for cert, player in certs:
        channel_id = player.marketplace_channel_id
        if not channel_id:
            continue
        existing = db.execute(
            text(
                """
                SELECT id FROM marketplace_player_certifications
                WHERE channel_partner_id = :cid AND certification_type = :ctype
                """
            ),
            {"cid": channel_id, "ctype": cert.certification_type},
        ).first()
        if existing:
            db.execute(
                text(
                    """
                    UPDATE marketplace_player_certifications SET
                        status = :status, issuer = :issuer, issued_at = :issued_at, expires_at = :expires_at,
                        evidence_url = :evidence_url, partner_certification_id = :pid, source = 'PARTNER_MIRROR',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {
                    "id": existing[0],
                    "status": cert.status,
                    "issuer": cert.issuer,
                    "issued_at": cert.issued_at,
                    "expires_at": cert.expires_at,
                    "evidence_url": cert.evidence_url,
                    "pid": cert.id,
                },
            )
            cert.marketplace_certification_id = existing[0]
            updated += 1
        else:
            mid = new_id()
            db.execute(
                text(
                    """
                    INSERT INTO marketplace_player_certifications (
                        id, channel_partner_id, partner_code, certification_type, status, issuer,
                        issued_at, expires_at, evidence_url, partner_certification_id, source
                    ) VALUES (
                        :id, :cid, :code, :ctype, :status, :issuer,
                        :issued_at, :expires_at, :evidence_url, :pid, 'PARTNER_MIRROR'
                    )
                    """
                ),
                {
                    "id": mid,
                    "cid": channel_id,
                    "code": player.code,
                    "ctype": cert.certification_type,
                    "status": cert.status,
                    "issuer": cert.issuer,
                    "issued_at": cert.issued_at,
                    "expires_at": cert.expires_at,
                    "evidence_url": cert.evidence_url,
                    "pid": cert.id,
                },
            )
            cert.marketplace_certification_id = mid
            created += 1
    return {"created": created, "updated": updated}


def mirror_certifications_bidirectional(db: Session) -> dict:
    to_partner = mirror_certifications_from_marketplace(db)
    to_marketplace = mirror_certifications_to_marketplace(db)
    return {"from_marketplace": to_partner, "to_marketplace": to_marketplace}


def list_corridor_sla(db: Session, *, compliance_status: str | None = None, limit: int = 50) -> list[PartnerCorridorSla]:
    q = db.query(PartnerCorridorSla)
    if compliance_status:
        q = q.filter(PartnerCorridorSla.compliance_status == compliance_status.upper())
    return q.order_by(PartnerCorridorSla.corridor_code).limit(limit).all()


def _band(score: float, blockers: list[str]) -> str:
    if blockers and score < 40:
        return BAND_BLOCKED
    if score >= 75 and not blockers:
        return BAND_GO_LIVE
    if score >= 50:
        return BAND_PILOT
    if score >= 25:
        return BAND_PLANNED
    return BAND_BLOCKED


def recompute_ecosystem_readiness(db: Session) -> dict[str, int]:
    players = db.query(PartnerEcosystemPlayer).filter(PartnerEcosystemPlayer.active.is_(True)).all()
    updated = 0
    for p in players:
        cert_count = (
            db.query(PartnerPlayerCertification)
            .filter(
                PartnerPlayerCertification.ecosystem_player_id == p.id,
                PartnerPlayerCertification.status == "VALID",
            )
            .count()
        )
        score_cert = min(25.0, cert_count * 8.0)

        prod_caps = (
            db.query(PartnerPlayerCapability)
            .filter(
                PartnerPlayerCapability.ecosystem_player_id == p.id,
                PartnerPlayerCapability.enabled.is_(True),
                PartnerPlayerCapability.production_ready.is_(True),
            )
            .count()
        )
        sandbox_caps = (
            db.query(PartnerPlayerCapability)
            .filter(
                PartnerPlayerCapability.ecosystem_player_id == p.id,
                PartnerPlayerCapability.enabled.is_(True),
            )
            .count()
        )
        score_cap = min(35.0, prod_caps * 10.0 + min(10.0, sandbox_caps * 2.0))

        corridor_roles = (
            db.query(PartnerGlobalCorridor)
            .filter(
                PartnerGlobalCorridor.active.is_(True),
                (PartnerGlobalCorridor.primary_player_id == p.id) | (PartnerGlobalCorridor.fallback_player_id == p.id),
            )
            .count()
        )
        score_corridor = min(20.0, corridor_roles * 10.0)

        wh = (
            db.query(PartnerCapabilityWebhook)
            .filter(PartnerCapabilityWebhook.ecosystem_player_id == p.id, PartnerCapabilityWebhook.active.is_(True))
            .first()
        )
        score_wh = 0.0
        blockers: list[str] = []
        if wh:
            if wh.last_http_status and 200 <= wh.last_http_status < 300:
                score_wh = 20.0
            elif wh.last_http_status:
                score_wh = 5.0
                blockers.append("webhook_last_error")
            else:
                score_wh = 10.0
        elif p.code in CERTIFICATIONS_BY_PLAYER:
            blockers.append("missing_capability_webhook")

        if cert_count == 0 and p.global_tier in ("GLOBAL", "MULTI_REGION"):
            blockers.append("missing_certifications")
        if sandbox_caps == 0 and p.parent_group in ("MARKETPLACE", "LOCKER_NETWORK"):
            blockers.append("no_capabilities")

        score_total = min(100.0, score_cert + score_cap + score_corridor + score_wh)
        band = _band(score_total, blockers)

        row = db.get(PartnerEcosystemReadiness, p.id)
        payload = dict(
            player_code=p.code,
            score_total=score_total,
            score_certifications=score_cert,
            score_capabilities=score_cap,
            score_corridors=score_corridor,
            score_webhooks=score_wh,
            readiness_band=band,
            blockers_json=json.dumps(blockers),
            computed_at=_utcnow(),
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(PartnerEcosystemReadiness(ecosystem_player_id=p.id, **payload))
        updated += 1
    return {"updated": updated}


def recompute_relation_health(db: Session) -> dict[str, int]:
    players = _player_map(db)
    unhealthy_codes: set[str] = set()
    for code, p in players.items():
        wh = (
            db.query(PartnerCapabilityWebhook)
            .filter(PartnerCapabilityWebhook.ecosystem_player_id == p.id, PartnerCapabilityWebhook.active.is_(True))
            .first()
        )
        if wh and wh.last_http_status and wh.last_http_status >= 500:
            unhealthy_codes.add(code)

    relations = db.query(PartnerPlayerRelation).filter(PartnerPlayerRelation.active.is_(True)).all()
    updated = 0
    for rel in relations:
        from_p = db.get(PartnerEcosystemPlayer, rel.from_player_id)
        to_p = db.get(PartnerEcosystemPlayer, rel.to_player_id)
        if not from_p or not to_p:
            continue
        status = "HEALTHY"
        cascade = None
        details: dict = {}
        if from_p.code in unhealthy_codes:
            status = "OUTAGE"
            cascade = from_p.code
            details["reason"] = "upstream_webhook_failure"
        elif to_p.code in unhealthy_codes and rel.relation_type in ("AGGREGATES", "USES_CARRIER"):
            status = "DEGRADED"
            cascade = to_p.code
            details["reason"] = "downstream_dependency_degraded"

        row = db.query(PartnerRelationHealth).filter(PartnerRelationHealth.relation_id == rel.id).first()
        payload = dict(
            from_player_code=from_p.code,
            to_player_code=to_p.code,
            relation_type=rel.relation_type,
            health_status=status,
            cascade_from_player_code=cascade,
            last_check_at=_utcnow(),
            details_json=json.dumps(details),
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(PartnerRelationHealth(id=new_id(), relation_id=rel.id, **payload))
        updated += 1
    return {"updated": updated}


def global_ops_summary(db: Session) -> dict:
    bands = (
        db.query(PartnerEcosystemReadiness.readiness_band, PartnerEcosystemReadiness.ecosystem_player_id)
        .all()
    )
    by_band: dict[str, int] = {}
    for band, _ in bands:
        by_band[band] = by_band.get(band, 0) + 1
    mirrored = (
        db.query(PartnerPlayerCertification)
        .filter(PartnerPlayerCertification.marketplace_certification_id.isnot(None))
        .count()
    )
    return {
        "certifications": db.query(PartnerPlayerCertification).count(),
        "certifications_valid": db.query(PartnerPlayerCertification)
        .filter(PartnerPlayerCertification.status == "VALID")
        .count(),
        "corridors_active": db.query(PartnerGlobalCorridor).filter(PartnerGlobalCorridor.active.is_(True)).count(),
        "corridor_sla_rows": db.query(PartnerCorridorSla).count(),
        "certifications_mirrored": mirrored,
        "readiness_by_band": by_band,
        "relation_health": {
            "HEALTHY": db.query(PartnerRelationHealth).filter(PartnerRelationHealth.health_status == "HEALTHY").count(),
            "DEGRADED": db.query(PartnerRelationHealth).filter(PartnerRelationHealth.health_status == "DEGRADED").count(),
            "OUTAGE": db.query(PartnerRelationHealth).filter(PartnerRelationHealth.health_status == "OUTAGE").count(),
        },
    }


def list_certifications(db: Session, *, player_code: str | None = None, limit: int = 200) -> list[PartnerPlayerCertification]:
    q = db.query(PartnerPlayerCertification)
    if player_code:
        q = q.filter(PartnerPlayerCertification.player_code == player_code.upper())
    return q.order_by(PartnerPlayerCertification.player_code).limit(limit).all()


def list_corridors(
    db: Session, *, origin: str | None = None, dest: str | None = None, active_only: bool = True, limit: int = 100
) -> list[PartnerGlobalCorridor]:
    q = db.query(PartnerGlobalCorridor)
    if active_only:
        q = q.filter(PartnerGlobalCorridor.active.is_(True))
    if origin:
        q = q.filter(PartnerGlobalCorridor.origin_country == origin.upper())
    if dest:
        q = q.filter(PartnerGlobalCorridor.dest_country == dest.upper())
    return q.order_by(PartnerGlobalCorridor.priority, PartnerGlobalCorridor.corridor_code).limit(limit).all()


def list_ecosystem_readiness(
    db: Session, *, band: str | None = None, limit: int = 100
) -> list[PartnerEcosystemReadiness]:
    q = db.query(PartnerEcosystemReadiness)
    if band:
        q = q.filter(PartnerEcosystemReadiness.readiness_band == band.upper())
    return q.order_by(PartnerEcosystemReadiness.score_total.desc()).limit(limit).all()


def list_relation_health(
    db: Session, *, status: str | None = None, limit: int = 100
) -> list[PartnerRelationHealth]:
    q = db.query(PartnerRelationHealth)
    if status:
        q = q.filter(PartnerRelationHealth.health_status == status.upper())
    return q.order_by(PartnerRelationHealth.last_check_at.desc()).limit(limit).all()
