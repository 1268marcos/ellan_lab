# 01_source/order_pickup_service/app/services/antifraud_kiosk.py
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.kiosk_antifraud_event import KioskAntifraudEvent


# Ajuste fino (sugestão prática)
WINDOW_SEC = 60           # janela de 60s
MAX_EVENTS_PER_WINDOW = 6 # acima disso, bloqueia
BLOCK_SEC = 90            # bloqueio curto (90s)


def _hash(v: str) -> str:
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def check_kiosk_antifraud(
    db: Session,
    request: Request,
    totem_id: str,
    region: str,
    device_fingerprint: str | None,
) -> None:
    ip = request.client.host if request.client else "unknown"
    fp = device_fingerprint or "missing_fp"

    fp_hash = _hash(fp)
    ip_hash = _hash(ip)

    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(seconds=WINDOW_SEC)).replace(tzinfo=None)

    # 1) se está bloqueado, nega rápido
    active_block = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.blocked_until.isnot(None),
            KioskAntifraudEvent.blocked_until > now.replace(tzinfo=None),
        )
        .order_by(KioskAntifraudEvent.created_at.desc())
        .first()
    )
    if active_block:
        raise HTTPException(status_code=429, detail="kiosk rate limited (temporary block)")

    # 2) conta eventos na janela
    count_recent = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.created_at >= window_start,
        )
        .count()
    )

    # 3) registra evento
    ev = KioskAntifraudEvent.new(
        fp_hash=fp_hash,
        ip_hash=ip_hash,
        totem_id=totem_id,
        region=region,
        created_at=now.replace(tzinfo=None),
        blocked_until=None,
    )

    # 4) bloqueia se excedeu
    if count_recent + 1 > MAX_EVENTS_PER_WINDOW:
        ev.blocked_until = (now + timedelta(seconds=BLOCK_SEC)).replace(tzinfo=None)

    db.add(ev)
    db.commit()

    if ev.blocked_until:
        raise HTTPException(status_code=429, detail="kiosk rate limited (too many attempts)")