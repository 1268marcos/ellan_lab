from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.data.capability_webhook_events import CAPABILITY_EVENT_TYPES, DEFAULT_EVENTS, WEBHOOK_CAPABILITIES
from app.models.partner_capability_webhook import PartnerCapabilityWebhook, PartnerCapabilityWebhookDelivery
from app.models.partner_ecosystem import PartnerEcosystemPlayer
from app.models.partner_ecosystem_professional import PartnerPlayerCapability
from app.services.crypto_util import hash_secret, new_id
from app.services import webhook_dlq
from app.services.webhook_dispatch import dispatch_webhook

EVENT_CAPABILITY_HEALTH = "capability.health"
EVENT_TEST_PING = "webhook.test"
EVENT_READINESS_SCORE_DROP = "readiness.score_drop"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _events_for_capability(capability_code: str) -> list[str]:
    return CAPABILITY_EVENT_TYPES.get(capability_code, list(DEFAULT_EVENTS))


def _ingress_url(player_code: str, capability_code: str) -> str:
    base = get_settings().webhook_ingress_base_url.rstrip("/")
    return f"{base}/{player_code}/{capability_code}"


def _marketplace_table_exists(db: Session) -> bool:
    from app.core.database import Base

    if "marketplace_capability_webhooks" in Base.metadata.tables:
        return True
    try:
        bind = db.get_bind()
        return inspect(bind).has_table("marketplace_capability_webhooks")
    except Exception:
        return False


def _lookup_marketplace_webhook(db: Session, channel_partner_id: str | None, capability_code: str) -> dict | None:
    if not channel_partner_id or not _marketplace_table_exists(db):
        return None
    row = db.execute(
        text(
            """
            SELECT id, url, secret_key, event_types_json, active
            FROM marketplace_capability_webhooks
            WHERE channel_partner_id = :pid AND capability_code = :cap AND active = true
            LIMIT 1
            """
        ),
        {"pid": channel_partner_id, "cap": capability_code},
    ).mappings().first()
    return dict(row) if row else None


def _resolve_webhook_url(
    db: Session,
    player: PartnerEcosystemPlayer,
    capability_code: str,
    protocol: str,
) -> tuple[str, str, str | None]:
    """Retorna (url, source, marketplace_webhook_id)."""
    mkt = _lookup_marketplace_webhook(db, player.marketplace_channel_id, capability_code)
    if mkt:
        return mkt["url"], "MARKETPLACE_MIRROR", mkt["id"]

    if protocol == "WEBHOOK" or capability_code in WEBHOOK_CAPABILITIES:
        if player.global_tier == "PRIORITY" and get_settings().webhook_sandbox_fallback_url:
            return get_settings().webhook_sandbox_fallback_url, "SANDBOX_HTTPBIN", None
        return _ingress_url(player.code, capability_code), "INGRESS", None

    return _ingress_url(player.code, capability_code), "INGRESS_HEALTH", None


def configure_capability_webhook(
    db: Session,
    *,
    ecosystem_player_id: str,
    capability_code: str,
    url: str,
    secret: str | None = None,
    events: list[str] | None = None,
    source: str = "MANUAL",
    marketplace_webhook_id: str | None = None,
    active: bool = True,
) -> PartnerCapabilityWebhook:
    player = db.get(PartnerEcosystemPlayer, ecosystem_player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecosystem_player_not_found")
    secret_val = secret or f"whsec_{player.code.lower()}_{capability_code.lower()}"
    secret_hash = hash_secret(secret_val)
    events_json = json.dumps(events or _events_for_capability(capability_code))
    now = _utcnow()
    row = (
        db.query(PartnerCapabilityWebhook)
        .filter(
            PartnerCapabilityWebhook.ecosystem_player_id == ecosystem_player_id,
            PartnerCapabilityWebhook.capability_code == capability_code,
        )
        .first()
    )
    if row:
        row.url = url
        row.secret_hash = secret_hash
        row.secret_key = secret_val[:256]
        row.event_types_json = events_json
        row.source = source
        row.marketplace_webhook_id = marketplace_webhook_id
        row.active = active
        row.updated_at = now
    else:
        row = PartnerCapabilityWebhook(
            id=new_id(),
            ecosystem_player_id=ecosystem_player_id,
            player_code=player.code,
            capability_code=capability_code,
            url=url,
            secret_hash=secret_hash,
            secret_key=secret_val[:256],
            event_types_json=events_json,
            source=source,
            marketplace_webhook_id=marketplace_webhook_id,
            active=active,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mirror_webhooks_from_capabilities(db: Session) -> dict[str, int]:
    """Cria/atualiza webhooks para cada capability habilitada (espelho marketplace quando existir)."""
    created = updated = mirrored = 0
    rows = (
        db.query(PartnerPlayerCapability, PartnerEcosystemPlayer)
        .join(PartnerEcosystemPlayer, PartnerPlayerCapability.ecosystem_player_id == PartnerEcosystemPlayer.id)
        .filter(PartnerPlayerCapability.enabled.is_(True))
        .all()
    )
    for cap, player in rows:
        if cap.protocol not in ("WEBHOOK", "REST", "OAUTH2") and cap.capability_code not in WEBHOOK_CAPABILITIES:
            continue
        url, source, mkt_id = _resolve_webhook_url(db, player, cap.capability_code, cap.protocol)
        secret = None
        events = _events_for_capability(cap.capability_code)
        if source == "MARKETPLACE_MIRROR":
            mkt = _lookup_marketplace_webhook(db, player.marketplace_channel_id, cap.capability_code)
            if mkt:
                secret = mkt.get("secret_key")
                try:
                    events = json.loads(mkt.get("event_types_json") or "[]") or events
                except json.JSONDecodeError:
                    pass
            mirrored += 1

        had = (
            db.query(PartnerCapabilityWebhook)
            .filter(
                PartnerCapabilityWebhook.ecosystem_player_id == player.id,
                PartnerCapabilityWebhook.capability_code == cap.capability_code,
            )
            .first()
            is not None
        )
        configure_capability_webhook(
            db,
            ecosystem_player_id=player.id,
            capability_code=cap.capability_code,
            url=url,
            secret=secret,
            events=events,
            source=source,
            marketplace_webhook_id=mkt_id,
        )
        if had:
            updated += 1
        else:
            created += 1
    return {"created": created, "updated": updated, "mirrored_from_marketplace": mirrored, "total": created + updated}


def list_capability_webhooks(
    db: Session,
    *,
    ecosystem_player_id: str | None = None,
    player_code: str | None = None,
) -> list[PartnerCapabilityWebhook]:
    q = db.query(PartnerCapabilityWebhook)
    if ecosystem_player_id:
        q = q.filter(PartnerCapabilityWebhook.ecosystem_player_id == ecosystem_player_id)
    if player_code:
        q = q.filter(PartnerCapabilityWebhook.player_code == player_code.upper())
    return q.order_by(PartnerCapabilityWebhook.player_code, PartnerCapabilityWebhook.capability_code).all()


def test_capability_webhook(db: Session, webhook_id: str) -> PartnerCapabilityWebhookDelivery:
    row = db.get(PartnerCapabilityWebhook, webhook_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="capability_webhook_not_found")
    return deliver_event(
        db,
        row,
        EVENT_TEST_PING,
        {
            "player_code": row.player_code,
            "capability_code": row.capability_code,
            "ping": True,
        },
        force=True,
    )


def deliver_event(
    db: Session,
    webhook: PartnerCapabilityWebhook,
    event_type: str,
    payload: dict[str, Any],
    *,
    force: bool = False,
) -> PartnerCapabilityWebhookDelivery:
    try:
        subscribed = json.loads(webhook.event_types_json or "[]")
    except json.JSONDecodeError:
        subscribed = []
    if not force and event_type not in subscribed:
        st = webhook_dlq.STATUS_SKIPPED
        delivery = PartnerCapabilityWebhookDelivery(
            id=new_id(),
            webhook_id=webhook.id,
            event_type=event_type,
            payload_json=json.dumps(payload),
            success=False,
            response_snippet="event_not_subscribed",
            status=st,
            attempt_count=1,
        )
        db.add(delivery)
        db.commit()
        return delivery

    if not get_settings().webhook_dispatch_enabled:
        ok, http_status, snippet = True, 202, "dispatch_disabled_simulated"
    else:
        ok, http_status, snippet = dispatch_webhook(
            webhook.url,
            event_type,
            payload,
            secret=webhook.secret_key,
        )

    now = _utcnow()
    webhook.last_http_status = http_status
    webhook.last_delivered_at = now if ok else webhook.last_delivered_at
    webhook.last_error = None if ok else snippet
    webhook.updated_at = now
    st = webhook_dlq.apply_delivery_status(db, webhook_id=webhook.id, success=ok, response_snippet=snippet)
    delivery = PartnerCapabilityWebhookDelivery(
        id=new_id(),
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=json.dumps(payload),
        http_status=http_status,
        success=ok,
        response_snippet=snippet,
        status=st,
        attempt_count=1,
        dead_lettered_at=webhook_dlq.dead_lettered_at_for_status(st),
        created_at=now,
    )
    db.add(delivery)
    db.commit()
    return delivery


def list_deliveries(
    db: Session,
    *,
    status: str | None = None,
    webhook_id: str | None = None,
    limit: int = 100,
) -> list[PartnerCapabilityWebhookDelivery]:
    q = db.query(PartnerCapabilityWebhookDelivery)
    if status:
        q = q.filter(PartnerCapabilityWebhookDelivery.status == status.upper())
    if webhook_id:
        q = q.filter(PartnerCapabilityWebhookDelivery.webhook_id == webhook_id)
    return q.order_by(PartnerCapabilityWebhookDelivery.created_at.desc()).limit(limit).all()


def replay_delivery(db: Session, delivery_id: str) -> PartnerCapabilityWebhookDelivery:
    original = db.get(PartnerCapabilityWebhookDelivery, delivery_id)
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery_not_found")
    if original.status not in (webhook_dlq.STATUS_DEAD_LETTER, webhook_dlq.STATUS_FAILED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="delivery_not_replayable")
    webhook = db.get(PartnerCapabilityWebhook, original.webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    try:
        payload = json.loads(original.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    payload["replay"] = True
    payload["replay_of_delivery_id"] = original.id
    return _replay_deliver(db, webhook, original.event_type, payload, replay_of=original.id, attempt_count=original.attempt_count + 1)


def replay_dead_letter_batch(db: Session, *, limit: int = 25) -> dict[str, int]:
    rows = list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER, limit=limit)
    replayed = 0
    succeeded = 0
    for row in rows:
        try:
            d = replay_delivery(db, row.id)
            replayed += 1
            if d.success:
                succeeded += 1
        except HTTPException:
            continue
    return {"requested": len(rows), "replayed": replayed, "succeeded": succeeded}


def _replay_deliver(
    db: Session,
    webhook: PartnerCapabilityWebhook,
    event_type: str,
    payload: dict[str, Any],
    *,
    replay_of: str,
    attempt_count: int,
) -> PartnerCapabilityWebhookDelivery:
    if not get_settings().webhook_dispatch_enabled:
        ok, http_status, snippet = True, 202, "dispatch_disabled_simulated"
    else:
        ok, http_status, snippet = dispatch_webhook(
            webhook.url,
            event_type,
            payload,
            secret=webhook.secret_key,
        )
    now = _utcnow()
    st = webhook_dlq.apply_delivery_status(db, webhook_id=webhook.id, success=ok, response_snippet=snippet)
    webhook.last_http_status = http_status
    webhook.last_delivered_at = now if ok else webhook.last_delivered_at
    webhook.last_error = None if ok else snippet
    webhook.updated_at = now
    delivery = PartnerCapabilityWebhookDelivery(
        id=new_id(),
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=json.dumps(payload),
        http_status=http_status,
        success=ok,
        response_snippet=snippet,
        status=st,
        attempt_count=attempt_count,
        dead_lettered_at=webhook_dlq.dead_lettered_at_for_status(st),
        replay_of_delivery_id=replay_of,
        created_at=now,
    )
    db.add(delivery)
    db.commit()
    return delivery


def dispatch_player_capability_event(
    db: Session,
    player_code: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    capability_code: str | None = None,
) -> int:
    q = db.query(PartnerCapabilityWebhook).filter(
        PartnerCapabilityWebhook.player_code == player_code.upper(),
        PartnerCapabilityWebhook.active.is_(True),
    )
    if capability_code:
        q = q.filter(PartnerCapabilityWebhook.capability_code == capability_code)
    sent = 0
    for hook in q.all():
        deliver_event(db, hook, event_type, payload)
        sent += 1
    return sent
