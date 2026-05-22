from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.marketplace_alerts_webhooks import (
    MarketplaceCapabilityWebhook,
    MarketplaceReadinessAlert,
    MarketplaceReadinessScoreHistory,
)
from app.services import capability_webhook_service
from app.services.crypto_util import new_id

SCORE_DROP_THRESHOLD = 5.0
BAND_RANK = {"GO_LIVE": 0, "PILOT": 1, "PLANNED": 2, "BLOCKED": 3}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _band_worsened(previous: str | None, new: str) -> bool:
    if not previous:
        return False
    return BAND_RANK.get(new, 99) > BAND_RANK.get(previous, 0)


def _severity_for_drop(delta: float, band_worsened: bool) -> str:
    if band_worsened or delta >= 15:
        return "CRITICAL"
    if delta >= 8:
        return "WARNING"
    return "INFO"


def record_score_and_check_alerts(
    db: Session,
    *,
    channel_partner_id: str,
    partner_code: str,
    previous_score: float | None,
    previous_band: str | None,
    new_score: float,
    new_band: str,
) -> dict[str, int]:
    """Grava historico; cria alerta e dispara webhooks se score caiu."""
    alerts_created = 0
    webhooks_sent = 0

    db.add(
        MarketplaceReadinessScoreHistory(
            id=new_id(),
            channel_partner_id=channel_partner_id,
            partner_code=partner_code,
            score_total=new_score,
            readiness_band=new_band,
            recorded_at=_utcnow(),
        )
    )

    if previous_score is not None:
        prev_score = previous_score
        prev_band = previous_band
        delta = round(prev_score - new_score, 2)
        worsened = _band_worsened(prev_band, new_band)
        if delta >= SCORE_DROP_THRESHOLD or worsened:
            severity = _severity_for_drop(delta, worsened)
            alert = MarketplaceReadinessAlert(
                id=new_id(),
                channel_partner_id=channel_partner_id,
                partner_code=partner_code,
                alert_type="BAND_DOWNGRADE" if worsened and delta < SCORE_DROP_THRESHOLD else "SCORE_DROP",
                severity=severity,
                previous_score=prev_score,
                new_score=new_score,
                score_delta=delta,
                previous_band=prev_band,
                new_band=new_band,
                status="OPEN",
                details_json=json.dumps(
                    {
                        "threshold": SCORE_DROP_THRESHOLD,
                        "band_worsened": worsened,
                    }
                ),
            )
            db.add(alert)
            alerts_created += 1
            db.flush()

            payload = {
                "partner_code": partner_code,
                "alert_id": alert.id,
                "previous_score": prev_score,
                "new_score": new_score,
                "score_delta": delta,
                "previous_band": prev_band,
                "new_band": new_band,
                "severity": severity,
            }
            sent = capability_webhook_service.dispatch_partner_event(
                db,
                channel_partner_id,
                capability_webhook_service.EVENT_READINESS_SCORE_DROP,
                payload,
            )
            alert.webhook_dispatched = sent > 0
            webhooks_sent += sent

    return {"alerts_created": alerts_created, "webhooks_sent": webhooks_sent}


def list_readiness_alerts(db: Session, *, open_only: bool = True, limit: int = 100) -> list[MarketplaceReadinessAlert]:
    q = db.query(MarketplaceReadinessAlert)
    if open_only:
        q = q.filter(MarketplaceReadinessAlert.status == "OPEN")
    return q.order_by(MarketplaceReadinessAlert.created_at.desc()).limit(limit).all()


def acknowledge_alert(db: Session, alert_id: str) -> MarketplaceReadinessAlert:
    row = db.get(MarketplaceReadinessAlert, alert_id)
    if not row:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert_not_found")
    row.status = "ACKNOWLEDGED"
    row.acknowledged_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


WEBHOOK_CAPABILITY_CODES = frozenset(
    {"ORDERS_WEBHOOK", "TRACKING_PUSH", "SETTLEMENT_FEED", "DELIVERY_STATUS"}
)


def _default_webhook_url(partner_code: str, capability_code: str) -> str:
    from app.core.config import get_settings

    base = getattr(get_settings(), "webhook_ingress_base_url", None)
    if base:
        return f"{base.rstrip('/')}/{partner_code}/{capability_code}"
    return "https://httpbin.org/post"


def seed_capability_webhooks_from_catalog(db: Session) -> dict[str, int]:
    """Um webhook por capability com protocolo WEBHOOK ou código de evento inbound."""
    from app.models.marketplace_extended import MarketplaceChannelCapability, MarketplaceChannelPartner

    created = skipped = 0
    rows = (
        db.query(MarketplaceChannelCapability, MarketplaceChannelPartner)
        .join(
            MarketplaceChannelPartner,
            MarketplaceChannelCapability.channel_partner_id == MarketplaceChannelPartner.id,
        )
        .filter(
            MarketplaceChannelCapability.enabled.is_(True),
            MarketplaceChannelPartner.active.is_(True),
        )
        .all()
    )
    for cap, partner in rows:
        if cap.protocol != "WEBHOOK" and cap.capability_code not in WEBHOOK_CAPABILITY_CODES:
            continue
        exists = (
            db.query(MarketplaceCapabilityWebhook)
            .filter(
                MarketplaceCapabilityWebhook.channel_partner_id == partner.id,
                MarketplaceCapabilityWebhook.capability_code == cap.capability_code,
            )
            .first()
        )
        if exists:
            skipped += 1
            continue
        capability_webhook_service.configure_capability_webhook(
            db,
            channel_partner_id=partner.id,
            capability_code=cap.capability_code,
            url=_default_webhook_url(partner.code, cap.capability_code),
            secret=f"whsec_{partner.code.lower()}_{cap.capability_code.lower()}",
            events=[
                capability_webhook_service.EVENT_READINESS_SCORE_DROP,
                capability_webhook_service.EVENT_CAPABILITY_HEALTH,
                capability_webhook_service.EVENT_TEST_PING,
            ],
        )
        created += 1
    return {"created": created, "skipped": skipped, "total": created + skipped}


def seed_demo_capability_webhooks(db: Session) -> int:
    """Compat: garante demos + sincroniza catálogo completo de webhooks por capability."""
    from app.services.extended_service import seed_channel_players

    seed_channel_players(db, refresh_existing=True)
    stats = seed_capability_webhooks_from_catalog(db)
    return stats["created"]
