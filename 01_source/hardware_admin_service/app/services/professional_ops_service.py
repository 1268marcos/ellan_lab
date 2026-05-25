from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

_SRC_ROOT = Path(__file__).resolve().parents[3]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from shared.integration.capability_bridge import marketplace_code_for_hardware, score_player_readiness  # noqa: E402

from app.data.professional_ops_seed import (
    DEMO_INCIDENTS,
    DEMO_WEBHOOKS,
    LOCKER_CORRIDORS,
    ONBOARDING_PLAYBOOKS,
    PLAYER_CERTIFICATIONS,
)
from app.models.cross_domain import HardwareEcosystemPlayer
from app.models.hardware_ops import HardwareSyncQueue, HardwareTelemetryEvent
from app.models.integration import HardwarePlayerIntegrationCapability
from app.models.professional_ops import (
    HardwareCapabilityWebhook,
    HardwareCapabilityWebhookDelivery,
    HardwareCorridorHandoffStep,
    HardwareCorridorSla,
    HardwareIntegrationIncident,
    HardwareIntegrationReadiness,
    HardwareLockerCorridor,
    HardwareOnboardingMilestone,
    HardwareOnboardingPlaybook,
    HardwareOnboardingRun,
    HardwarePlayerCertification,
    HardwareReadinessAlert,
    HardwareSyncAuditLog,
)
from app.schemas.professional_ops import HardwareProfessionalOpsSummaryOut
from app.services.crypto_util import new_id

DEMO_LOCKER = "LOCKER-DEMO-01"


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
        HardwareSyncAuditLog(
            id=new_id(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            summary=summary,
            payload_json=payload or {},
        )
    )


def recompute_readiness(db: Session, *, actor_id: str | None = None) -> dict[str, int]:
    updated = 0
    alerts = 0
    for player in db.query(HardwareEcosystemPlayer).all():
        caps = (
            db.query(HardwarePlayerIntegrationCapability)
            .filter(
                HardwarePlayerIntegrationCapability.player_id == player.id,
                HardwarePlayerIntegrationCapability.is_active.is_(True),
            )
            .all()
        )
        mkt_code = marketplace_code_for_hardware(player.player_code, player.marketplace_channel_code)
        regions = player.regions_json if isinstance(player.regions_json, list) else []
        score_total, score_cap, score_api, score_ops, band, blockers = score_player_readiness(
            capability_count=len(caps),
            integration_mode=player.integration_mode,
            parent_group=player.parent_group,
            supports_lockers=player.supports_lockers,
            operator_id=player.operator_id,
            regions_count=len(regions),
            marketplace_linked=bool(mkt_code),
        )
        prev = db.get(HardwareIntegrationReadiness, player.id)
        prev_score = float(prev.score_total) if prev else None
        prev_band = prev.readiness_band if prev else None

        row = prev or HardwareIntegrationReadiness(player_id=player.id, player_code=player.player_code)
        row.player_code = player.player_code
        row.score_total = score_total
        row.score_capabilities = score_cap
        row.score_api = score_api
        row.score_operations = score_ops
        row.readiness_band = band
        row.blockers_json = blockers
        row.marketplace_partner_code = mkt_code
        row.computed_at = _utcnow()
        if not prev:
            db.add(row)
        updated += 1

        if prev_score is not None and score_total < prev_score - 5:
            db.add(
                HardwareReadinessAlert(
                    id=new_id(),
                    player_id=player.id,
                    player_code=player.player_code,
                    alert_type="SCORE_DROP",
                    severity="CRITICAL" if band == "BLOCKED" else "WARNING",
                    previous_score=prev_score,
                    new_score=score_total,
                    score_delta=round(score_total - prev_score, 2),
                    previous_band=prev_band,
                    new_band=band,
                )
            )
            alerts += 1

    append_audit(
        db,
        event_type="READINESS_RECOMPUTE",
        entity_type="HARDWARE_INTEGRATION",
        summary=f"Recomputed readiness for {updated} players",
        actor_id=actor_id,
        payload={"updated": updated, "alerts": alerts},
    )
    db.commit()
    return {"updated": updated, "alerts_created": alerts}


def detect_incidents_from_signals(db: Session) -> int:
    """Auto-open incidents from sync queue + stale telemetry."""
    inserted = 0
    stale_sync = (
        db.query(HardwareSyncQueue)
        .filter(HardwareSyncQueue.status == "FAILED", HardwareSyncQueue.retry_count >= 3)
        .all()
    )
    for item in stale_sync:
        exists = (
            db.query(HardwareIntegrationIncident)
            .filter(
                HardwareIntegrationIncident.locker_id == item.locker_id,
                HardwareIntegrationIncident.incident_type == "SYNC_FAILED",
                HardwareIntegrationIncident.status == "OPEN",
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareIntegrationIncident(
                id=new_id(),
                locker_id=item.locker_id,
                severity="CRITICAL",
                incident_type="SYNC_FAILED",
                title=f"Sync failed after retries: {item.operation}",
                details_json={"sync_id": item.id, "retry_count": item.retry_count},
            )
        )
        inserted += 1

    cutoff = _utcnow() - timedelta(hours=2)
    stale_hb = (
        db.query(HardwareTelemetryEvent)
        .filter(HardwareTelemetryEvent.event_type == "HEARTBEAT", HardwareTelemetryEvent.created_at < cutoff)
        .order_by(HardwareTelemetryEvent.created_at.desc())
        .limit(5)
        .all()
    )
    for ev in stale_hb:
        exists = (
            db.query(HardwareIntegrationIncident)
            .filter(
                HardwareIntegrationIncident.locker_id == ev.locker_id,
                HardwareIntegrationIncident.incident_type == "OFFLINE",
                HardwareIntegrationIncident.status == "OPEN",
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareIntegrationIncident(
                id=new_id(),
                locker_id=ev.locker_id,
                severity="WARNING",
                incident_type="OFFLINE",
                title="Heartbeat stale > 2h",
                details_json={"last_event_id": ev.id},
            )
        )
        inserted += 1

    if inserted:
        append_audit(
            db,
            event_type="INCIDENT_DETECT",
            entity_type="HARDWARE_OPS",
            summary=f"Auto-detected {inserted} integration incidents",
            payload={"inserted": inserted},
        )
        db.commit()
    return inserted


def seed_professional_ops(db: Session) -> dict[str, int]:
    counts = {
        "playbooks": 0,
        "certifications": 0,
        "corridors": 0,
        "corridor_steps": 0,
        "corridor_sla": 0,
        "incidents": 0,
        "webhooks": 0,
        "onboarding_runs": 0,
        "onboarding_milestones": 0,
    }

    for pb in ONBOARDING_PLAYBOOKS:
        if db.get(HardwareOnboardingPlaybook, pb["code"]):
            continue
        db.add(HardwareOnboardingPlaybook(**pb))
        counts["playbooks"] += 1

    for pid, pcode, ctype, status, issuer, issued, expires in PLAYER_CERTIFICATIONS:
        exists = (
            db.query(HardwarePlayerCertification)
            .filter(
                HardwarePlayerCertification.player_id == pid,
                HardwarePlayerCertification.certification_type == ctype,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwarePlayerCertification(
                id=new_id(),
                player_id=pid,
                player_code=pcode,
                certification_type=ctype,
                status=status,
                issuer=issuer,
                issued_at=issued,
                expires_at=expires,
            )
        )
        counts["certifications"] += 1

    for spec in LOCKER_CORRIDORS:
        if db.get(HardwareLockerCorridor, spec["id"]):
            continue
        db.add(
            HardwareLockerCorridor(
                id=spec["id"],
                corridor_code=spec["corridor_code"],
                name=spec["name"],
                origin_country=spec["origin_country"],
                dest_country=spec["dest_country"],
                handoff_type=spec["handoff_type"],
                primary_player_id=spec["primary_player_id"],
                primary_player_code=spec["primary_player_code"],
                fallback_player_id=spec.get("fallback_player_id"),
                fallback_player_code=spec.get("fallback_player_code"),
                transit_hours_min=spec["transit_hours_min"],
                transit_hours_max=spec["transit_hours_max"],
                supports_returns=spec["supports_returns"],
                priority=spec["priority"],
            )
        )
        counts["corridors"] += 1
        for order, (step_pid, step_code, role, locker_id) in enumerate(spec["steps"], start=1):
            db.add(
                HardwareCorridorHandoffStep(
                    id=new_id(),
                    corridor_id=spec["id"],
                    step_order=order,
                    player_id=step_pid,
                    player_code=step_code,
                    step_role=role,
                    locker_id=locker_id,
                )
            )
            counts["corridor_steps"] += 1
        sla = spec["sla"]
        db.add(
            HardwareCorridorSla(
                id=new_id(),
                corridor_id=spec["id"],
                corridor_code=spec["corridor_code"],
                uptime_target_pct=sla.get("uptime_target_pct", 99.5),
                door_open_p95_ms=sla.get("door_open_p95_ms", 2500),
                sync_lag_max_sec=sla.get("sync_lag_max_sec", 300),
            )
        )
        counts["corridor_sla"] += 1

    for pid, pcode, locker_id, severity, itype, title in DEMO_INCIDENTS:
        exists = (
            db.query(HardwareIntegrationIncident)
            .filter(HardwareIntegrationIncident.title == title, HardwareIntegrationIncident.status == "OPEN")
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareIntegrationIncident(
                id=new_id(),
                player_id=pid,
                player_code=pcode,
                locker_id=locker_id,
                severity=severity,
                incident_type=itype,
                title=title,
            )
        )
        counts["incidents"] += 1

    for pid, pcode, cap_code, url in DEMO_WEBHOOKS:
        exists = (
            db.query(HardwareCapabilityWebhook)
            .filter(HardwareCapabilityWebhook.player_id == pid, HardwareCapabilityWebhook.capability_code == cap_code)
            .first()
        )
        if exists:
            continue
        secret = hashlib.sha256(f"{pcode}:{cap_code}".encode()).hexdigest()
        db.add(
            HardwareCapabilityWebhook(
                id=new_id(),
                player_id=pid,
                player_code=pcode,
                capability_code=cap_code,
                url=url,
                secret_hash=secret,
                secret_key=f"whsec_{pcode.lower()}_{cap_code.lower()}",
                event_types_json=["capability.health", "readiness.score_dropped", "webhook.test"],
                last_http_status=200,
                last_delivered_at=_utcnow(),
            )
        )
        counts["webhooks"] += 1

    run_id = "hw-onboard-demo-01"
    if not db.get(HardwareOnboardingRun, run_id):
        db.add(
            HardwareOnboardingRun(
                id=run_id,
                subject_type="LOCKER",
                subject_id=DEMO_LOCKER,
                playbook_code="LOCKER_GO_LIVE",
                status="IN_PROGRESS",
                current_step_order=4,
                blockers_json=["CERT_VALID pending"],
            )
        )
        counts["onboarding_runs"] += 1
        for order, step_code, status in [
            (1, "PROVISION_MQTT", "DONE"),
            (2, "SLOT_TOPOLOGY_SYNC", "DONE"),
            (3, "PAYMENT_BIND", "DONE"),
            (4, "MKT_LINK", "DONE"),
            (5, "CERT_VALID", "PENDING"),
            (6, "READINESS_GO_LIVE", "PENDING"),
        ]:
            db.add(
                HardwareOnboardingMilestone(
                    id=new_id(),
                    run_id=run_id,
                    step_code=step_code,
                    step_order=order,
                    status=status,
                    evidence_json={"seed": True} if status == "DONE" else {},
                    completed_at=_utcnow() if status == "DONE" else None,
                )
            )
            counts["onboarding_milestones"] += 1

    if any(counts.values()):
        append_audit(
            db,
            event_type="PROFESSIONAL_OPS_SEED",
            entity_type="HARDWARE_ADMIN",
            summary="Seeded professional ops catalog",
            payload=counts,
        )
        db.commit()

    recompute_readiness(db)
    detect_incidents_from_signals(db)
    return counts


def professional_ops_summary(db: Session) -> HardwareProfessionalOpsSummaryOut:
    rows = db.query(HardwareIntegrationReadiness).all()
    bands: dict[str, int] = {"GO_LIVE": 0, "PILOT": 0, "PLANNED": 0, "BLOCKED": 0}
    total = 0.0
    blockers = 0
    for r in rows:
        bands[r.readiness_band] = bands.get(r.readiness_band, 0) + 1
        total += float(r.score_total)
        if r.blockers_json:
            blockers += 1

    since = _utcnow() - timedelta(hours=24)
    return HardwareProfessionalOpsSummaryOut(
        readiness_rows=len(rows),
        avg_score=round(total / len(rows), 2) if rows else 0.0,
        bands=bands,
        open_incidents=db.query(HardwareIntegrationIncident).filter(HardwareIntegrationIncident.status == "OPEN").count(),
        open_readiness_alerts=db.query(HardwareReadinessAlert).filter(HardwareReadinessAlert.status == "OPEN").count(),
        partners_with_blockers=blockers,
        certifications=db.query(HardwarePlayerCertification).count(),
        corridors=db.query(HardwareLockerCorridor).filter(HardwareLockerCorridor.active.is_(True)).count(),
        corridor_sla_compliant=db.query(HardwareCorridorSla).filter(HardwareCorridorSla.compliance_status == "COMPLIANT").count(),
        onboarding_runs_active=db.query(HardwareOnboardingRun).filter(HardwareOnboardingRun.status == "IN_PROGRESS").count(),
        capability_webhooks=db.query(HardwareCapabilityWebhook).filter(HardwareCapabilityWebhook.active.is_(True)).count(),
        webhook_deliveries_24h=db.query(HardwareCapabilityWebhookDelivery)
        .filter(HardwareCapabilityWebhookDelivery.created_at >= since)
        .count(),
        audit_log_entries=db.query(HardwareSyncAuditLog).count(),
    )


def acknowledge_alert(db: Session, alert_id: str) -> HardwareReadinessAlert:
    row = db.get(HardwareReadinessAlert, alert_id)
    if not row:
        raise ValueError("alert_not_found")
    row.status = "ACKNOWLEDGED"
    db.commit()
    db.refresh(row)
    return row


def mirror_certifications_from_marketplace(db: Session) -> dict[str, int]:
    """GET certifications do marketplace_admin via HTTP e upsert em hardware_player_certifications."""
    import httpx
    from datetime import date as date_type

    from shared.integration.capability_bridge import MARKETPLACE_TO_HARDWARE_CODE

    from app.core.config import get_settings
    from app.models.cross_domain import HardwareEcosystemPlayer

    base = get_settings().marketplace_admin_url.rstrip("/")
    url = f"{base}/api/v1/marketplace-admin/global-ops/certifications"
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        append_audit(
            db,
            event_type="CERT_MIRROR_FAILED",
            entity_type="MARKETPLACE_ADMIN",
            summary=f"HTTP mirror failed: {exc}",
            payload={"url": url},
        )
        db.commit()
        raise ValueError(f"marketplace_unreachable: {exc}") from exc

    if not isinstance(payload, list):
        raise ValueError("invalid_marketplace_certifications_response")

    players_by_code = {p.player_code: p for p in db.query(HardwareEcosystemPlayer).all()}
    inserted = updated = skipped = 0

    def _parse_date(val: object) -> date_type | None:
        if val is None:
            return None
        if isinstance(val, date_type):
            return val
        if isinstance(val, str) and val:
            return date_type.fromisoformat(val[:10])
        return None

    for item in payload:
        mkt_code = str(item.get("partner_code") or "").upper()
        hw_code = MARKETPLACE_TO_HARDWARE_CODE.get(mkt_code, mkt_code)
        player = players_by_code.get(hw_code)
        if not player:
            skipped += 1
            continue

        cert_type = str(item.get("certification_type") or "")
        mkt_cert_id = str(item.get("id") or "")
        existing = None
        if mkt_cert_id:
            existing = (
                db.query(HardwarePlayerCertification)
                .filter(HardwarePlayerCertification.marketplace_cert_id == mkt_cert_id)
                .first()
            )
        if not existing:
            existing = (
                db.query(HardwarePlayerCertification)
                .filter(
                    HardwarePlayerCertification.player_id == player.id,
                    HardwarePlayerCertification.certification_type == cert_type,
                )
                .first()
            )

        fields = dict(
            player_id=player.id,
            player_code=player.player_code,
            certification_type=cert_type,
            status=str(item.get("status") or "VALID"),
            source="MARKETPLACE_MIRROR",
            marketplace_cert_id=mkt_cert_id or None,
            issuer=item.get("issuer"),
            issued_at=_parse_date(item.get("issued_at")),
            expires_at=_parse_date(item.get("expires_at")),
            evidence_url=item.get("evidence_url"),
            scope_notes=f"mirrored from marketplace partner {mkt_code}",
        )
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(HardwarePlayerCertification(id=new_id(), **fields))
            inserted += 1

    append_audit(
        db,
        event_type="CERT_MIRROR",
        entity_type="MARKETPLACE_ADMIN",
        summary=f"Mirrored {inserted + updated} certifications from marketplace ({skipped} skipped)",
        payload={"inserted": inserted, "updated": updated, "skipped": skipped, "url": url},
    )
    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "fetched": len(payload)}
