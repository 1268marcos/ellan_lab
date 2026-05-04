from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.delivery import Delivery
from app.models.manifest import Manifest


def create_manifest(db: Session, shipments: list[dict[str, Any]], locker_id: str, status: str = "draft") -> Manifest:
    m = Manifest(shipments=json.dumps(shipments), locker_id=locker_id, status=status)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_manifest(db: Session, manifest_id: str) -> Manifest | None:
    return db.get(Manifest, manifest_id)


def track_delivery(
    db: Session,
    tracking: str,
    manifest_id: str | None = None,
    eta: datetime | None = None,
    signature: str | None = None,
) -> Delivery:
    d = db.scalar(select(Delivery).where(Delivery.tracking == tracking))
    if d:
        if manifest_id is not None:
            d.manifest_id = manifest_id
        if eta is not None:
            d.eta = eta
        if signature is not None:
            d.signature = signature
        db.commit()
        db.refresh(d)
        return d
    d = Delivery(tracking=tracking, manifest_id=manifest_id, eta=eta, signature=signature)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def get_delivery(db: Session, delivery_id: str) -> Delivery | None:
    return db.get(Delivery, delivery_id)


def fetch_locker_status(locker_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.backend_runtime_base_url.rstrip('/')}/lockers/{locker_id}/status"
    try:
        c = client or httpx.Client(timeout=3.0)
        own = client is None
        try:
            r = c.get(url)
            if r.status_code == 200:
                return {"ok": True, "data": r.json()}
        finally:
            if own:
                c.close()
    except Exception:
        pass
    return {"ok": False, "data": None}
