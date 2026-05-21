from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook import LockerWebhookConfig
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services.crypto_util import hash_secret
from app.services.locker_service import get_locker_or_404


def configure_webhook(db: Session, locker_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_locker_or_404(db, locker_id)
    now = datetime.now(timezone.utc)
    events_csv = ",".join(body.events)
    secret_hash = hash_secret(body.secret) if body.secret else None
    row = db.query(LockerWebhookConfig).filter(LockerWebhookConfig.locker_id == locker_id).first()
    if row:
        row.url = str(body.url)
        row.secret_hash = secret_hash
        row.events = events_csv
        row.active = body.active
        row.updated_at = now
    else:
        row = LockerWebhookConfig(
            locker_id=locker_id,
            url=str(body.url),
            secret_hash=secret_hash,
            events=events_csv,
            active=body.active,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return WebhookOut(
        locker_id=locker_id,
        url=row.url,
        events=[e.strip() for e in row.events.split(",") if e.strip()],
        active=row.active,
        has_secret=bool(row.secret_hash),
        updated_at=row.updated_at,
    )


def get_webhook(db: Session, locker_id: str) -> WebhookOut | None:
    get_locker_or_404(db, locker_id)
    row = db.query(LockerWebhookConfig).filter(LockerWebhookConfig.locker_id == locker_id).first()
    if not row:
        return None
    return WebhookOut(
        locker_id=locker_id,
        url=row.url,
        events=[e.strip() for e in row.events.split(",") if e.strip()],
        active=row.active,
        has_secret=bool(row.secret_hash),
        updated_at=row.updated_at,
    )
