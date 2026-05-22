from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base
from app.data.global_ops_seed import CERTIFICATIONS_BY_PLAYER, CORRIDORS, CORRIDOR_SLA

_CROSS_SCHEMA_TABLES = frozenset(
    {"marketplace_player_certifications", "partner_player_certifications", "partner_ecosystem_players"}
)
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.models.marketplace_global_ops import (
    MarketplaceCorridorPlayerStep,
    MarketplaceCorridorSla,
    MarketplaceGlobalCorridor,
    MarketplacePlayerCertification,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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


def _partner_map(db: Session) -> dict[str, MarketplaceChannelPartner]:
    rows = db.query(MarketplaceChannelPartner).all()
    return {r.code.upper(): r for r in rows}


def seed_global_ops(db: Session) -> dict[str, int]:
    partners = _partner_map(db)
    certs = 0
    for code, items in CERTIFICATIONS_BY_PLAYER.items():
        ch = partners.get(code.upper())
        if not ch:
            continue
        for cert_type, issuer, status, years in items:
            issued = date.today() - timedelta(days=180)
            expires = date.today() + timedelta(days=365 * years)
            existing = (
                db.query(MarketplacePlayerCertification)
                .filter(
                    MarketplacePlayerCertification.channel_partner_id == ch.id,
                    MarketplacePlayerCertification.certification_type == cert_type,
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
                    MarketplacePlayerCertification(
                        id=new_id(),
                        channel_partner_id=ch.id,
                        partner_code=ch.code,
                        certification_type=cert_type,
                        status=status,
                        issuer=issuer,
                        issued_at=issued,
                        expires_at=expires,
                        evidence_url=f"https://compliance.example/{ch.code.lower()}/{cert_type.lower()}",
                    )
                )
            certs += 1

    corridors = 0
    steps = 0
    for spec in CORRIDORS:
        primary = partners.get(spec["primary"].upper())
        if not primary:
            continue
        fallback = partners.get(spec["fallback"].upper()) if spec.get("fallback") else None
        row = (
            db.query(MarketplaceGlobalCorridor)
            .filter(MarketplaceGlobalCorridor.corridor_code == spec["corridor_code"])
            .first()
        )
        payload = dict(
            name=spec["name"],
            origin_country=spec["origin_country"],
            dest_country=spec["dest_country"],
            primary_channel_partner_id=primary.id,
            primary_partner_code=primary.code,
            fallback_channel_partner_id=fallback.id if fallback else None,
            fallback_partner_code=fallback.code if fallback else None,
            handoff_type=spec["handoff_type"],
            service_level=spec["service_level"],
            transit_days_min=spec["transit_days_min"],
            transit_days_max=spec["transit_days_max"],
            supports_returns=spec.get("supports_returns", False),
            active=True,
            priority=spec.get("priority", 100),
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
            corridor_id = row.id
        else:
            corridor_id = new_id()
            db.add(MarketplaceGlobalCorridor(id=corridor_id, corridor_code=spec["corridor_code"], **payload))
        corridors += 1

        db.query(MarketplaceCorridorPlayerStep).filter(MarketplaceCorridorPlayerStep.corridor_id == corridor_id).delete()
        for order, (step_code, role) in enumerate(spec.get("steps") or [], start=1):
            step_ch = partners.get(step_code.upper())
            if not step_ch:
                continue
            db.add(
                MarketplaceCorridorPlayerStep(
                    id=new_id(),
                    corridor_id=corridor_id,
                    step_order=order,
                    channel_partner_id=step_ch.id,
                    partner_code=step_ch.code,
                    step_role=role,
                )
            )
            steps += 1

    db.flush()
    sla_rows = seed_corridor_sla(db)
    cert_mirror = mirror_certifications_from_partner(db)
    db.commit()
    return {
        "certifications": certs,
        "corridors": corridors,
        "corridor_steps": steps,
        "corridor_sla": sla_rows,
        "certifications_mirror": cert_mirror,
    }


def seed_corridor_sla(db: Session) -> int:
    count = 0
    for c in db.query(MarketplaceGlobalCorridor).filter(MarketplaceGlobalCorridor.active.is_(True)).all():
        spec = CORRIDOR_SLA.get(c.corridor_code, {})
        max_hours = spec.get("max_transit_hours") or max(c.transit_days_max * 24, 24)
        row = db.query(MarketplaceCorridorSla).filter(MarketplaceCorridorSla.corridor_id == c.id).first()
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
            db.add(MarketplaceCorridorSla(id=new_id(), corridor_id=c.id, **payload))
        count += 1
    return count


def mirror_certifications_from_partner(db: Session) -> dict[str, int]:
    if not _has_table(db, "partner_player_certifications"):
        return {"created": 0, "updated": 0, "skipped_no_table": 1}
    rows = db.execute(
        text(
            """
            SELECT p.id, p.ecosystem_player_id, p.player_code, p.certification_type, p.status, p.issuer,
                   p.issued_at, p.expires_at, p.evidence_url, p.marketplace_certification_id,
                   e.marketplace_channel_id
            FROM partner_player_certifications p
            JOIN partner_ecosystem_players e ON e.id = p.ecosystem_player_id
            WHERE e.marketplace_channel_id IS NOT NULL
            """
        )
    ).mappings().all()
    created = updated = 0
    for row in rows:
        channel_id = row["marketplace_channel_id"]
        if not channel_id:
            continue
        existing = (
            db.query(MarketplacePlayerCertification)
            .filter(
                MarketplacePlayerCertification.channel_partner_id == channel_id,
                MarketplacePlayerCertification.certification_type == row["certification_type"],
            )
            .first()
        )
        if existing:
            existing.status = row["status"]
            existing.issuer = row["issuer"]
            existing.issued_at = row["issued_at"]
            existing.expires_at = row["expires_at"]
            existing.evidence_url = row["evidence_url"]
            existing.partner_certification_id = row["id"]
            existing.source = "PARTNER_MIRROR"
            updated += 1
        else:
            db.add(
                MarketplacePlayerCertification(
                    id=new_id(),
                    channel_partner_id=channel_id,
                    partner_code=row["player_code"],
                    certification_type=row["certification_type"],
                    status=row["status"],
                    issuer=row["issuer"],
                    issued_at=row["issued_at"],
                    expires_at=row["expires_at"],
                    evidence_url=row["evidence_url"],
                    partner_certification_id=row["id"],
                    source="PARTNER_MIRROR",
                )
            )
            created += 1
    return {"created": created, "updated": updated}


def list_corridor_sla(db: Session, *, compliance_status: str | None = None, limit: int = 50) -> list[MarketplaceCorridorSla]:
    q = db.query(MarketplaceCorridorSla)
    if compliance_status:
        q = q.filter(MarketplaceCorridorSla.compliance_status == compliance_status.upper())
    return q.order_by(MarketplaceCorridorSla.corridor_code).limit(limit).all()


def global_ops_summary(db: Session) -> dict:
    mirrored = (
        db.query(MarketplacePlayerCertification)
        .filter(MarketplacePlayerCertification.partner_certification_id.isnot(None))
        .count()
    )
    return {
        "certifications": db.query(MarketplacePlayerCertification).count(),
        "certifications_valid": db.query(MarketplacePlayerCertification)
        .filter(MarketplacePlayerCertification.status == "VALID")
        .count(),
        "corridors_active": db.query(MarketplaceGlobalCorridor)
        .filter(MarketplaceGlobalCorridor.active.is_(True))
        .count(),
        "corridor_steps": db.query(MarketplaceCorridorPlayerStep).count(),
        "corridor_sla_rows": db.query(MarketplaceCorridorSla).count(),
        "certifications_mirrored": mirrored,
    }


def list_certifications(db: Session, *, partner_code: str | None = None, limit: int = 200):
    q = db.query(MarketplacePlayerCertification)
    if partner_code:
        q = q.filter(MarketplacePlayerCertification.partner_code == partner_code.upper())
    return q.order_by(MarketplacePlayerCertification.partner_code).limit(limit).all()


def list_corridors(db: Session, *, origin: str | None = None, dest: str | None = None, active_only: bool = True, limit: int = 100):
    q = db.query(MarketplaceGlobalCorridor)
    if active_only:
        q = q.filter(MarketplaceGlobalCorridor.active.is_(True))
    if origin:
        q = q.filter(MarketplaceGlobalCorridor.origin_country == origin.upper())
    if dest:
        q = q.filter(MarketplaceGlobalCorridor.dest_country == dest.upper())
    return q.order_by(MarketplaceGlobalCorridor.priority).limit(limit).all()


def list_corridor_steps(db: Session, corridor_id: str):
    return (
        db.query(MarketplaceCorridorPlayerStep)
        .filter(MarketplaceCorridorPlayerStep.corridor_id == corridor_id)
        .order_by(MarketplaceCorridorPlayerStep.step_order)
        .all()
    )
