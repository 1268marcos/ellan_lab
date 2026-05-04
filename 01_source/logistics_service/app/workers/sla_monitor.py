from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import Delivery
from app.services import sla_service


def overdue_without_signature(db: Session, now: datetime | None = None) -> list[Delivery]:
    t = now or datetime.now(timezone.utc)
    return list(
        db.scalars(
            select(Delivery).where(Delivery.eta.is_not(None), Delivery.eta < t, Delivery.signature.is_(None))
        ).all()
    )


def run_once(db: Session, client: httpx.Client | None = None) -> dict[str, int | float | bool]:
    compliance = sla_service.fetch_compliance(client)
    overdue = overdue_without_signature(db)
    return {
        "overdue_count": len(overdue),
        "compliance_pct": float(compliance.get("compliance_pct", 0.0) or 0.0),
        "lifecycle_ok": bool(compliance.get("ok")),
    }
