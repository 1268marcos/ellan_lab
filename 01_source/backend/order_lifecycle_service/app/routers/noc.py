from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.lifecycle import DomainEvent, EventStatus

router = APIRouter(prefix="/api/v1/noc", tags=["NOC"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat().replace("+00:00", "Z")


def _source_error(exc: Exception) -> dict[str, Any]:
    return {
        "status": "error",
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }


def _table_exists(db: Session, table_name: str) -> bool:
    exists = db.execute(
        text("SELECT to_regclass(:table_name) IS NOT NULL AS exists"),
        {"table_name": f"public.{table_name}"},
    ).scalar()
    return bool(exists)


def _runtime_lockers_summary(db: Session) -> dict[str, Any]:
    if not _table_exists(db, "runtime_lockers"):
        return {
            "status": "missing_table",
            "total": 0,
            "online": 0,
            "offline": 0,
            "source": "runtime_lockers",
        }

    row = db.execute(
        text(
            """
            SELECT
                COUNT(*)::integer AS total,
                COUNT(*) FILTER (
                    WHERE active IS TRUE AND runtime_enabled IS TRUE
                )::integer AS online,
                COUNT(*) FILTER (
                    WHERE active IS NOT TRUE OR runtime_enabled IS NOT TRUE
                )::integer AS offline
            FROM runtime_lockers
            """
        )
    ).mappings().one()

    return {
        "status": "ok",
        "total": int(row["total"] or 0),
        "online": int(row["online"] or 0),
        "offline": int(row["offline"] or 0),
        "source": "runtime_lockers",
    }


def _incidents_summary(db: Session) -> dict[str, Any]:
    deadline_row = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE status IN ('EXECUTING', 'FAILED')
                       OR (status = 'PENDING' AND due_at <= NOW())
                )::integer AS active,
                COUNT(*) FILTER (WHERE status = 'FAILED')::integer AS critical
            FROM lifecycle_deadlines
            """
        )
    ).mappings().one()

    event_row = db.execute(
        text(
            """
            SELECT COUNT(*)::integer AS failed
            FROM domain_events
            WHERE status = 'FAILED'
            """
        )
    ).mappings().one()

    deadline_active = int(deadline_row["active"] or 0)
    deadline_critical = int(deadline_row["critical"] or 0)
    failed_events = int(event_row["failed"] or 0)

    return {
        "status": "ok",
        "active": deadline_active + failed_events,
        "critical": deadline_critical + failed_events,
        "deadline_incidents": deadline_active,
        "failed_domain_events": failed_events,
        "source": "lifecycle_deadlines+domain_events",
    }


def _pickup_pending_summary(db: Session) -> dict[str, Any]:
    if not _table_exists(db, "pickups"):
        return {
            "status": "missing_table",
            "pending": 0,
            "overdue": 0,
            "source": "pickups",
        }

    row = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'ACTIVE')::integer AS pending,
                COUNT(*) FILTER (
                    WHERE status = 'ACTIVE' AND expires_at IS NOT NULL AND expires_at <= NOW()
                )::integer AS overdue
            FROM pickups
            """
        )
    ).mappings().one()

    return {
        "status": "ok",
        "pending": int(row["pending"] or 0),
        "overdue": int(row["overdue"] or 0),
        "source": "pickups",
    }


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/dashboard")
async def noc_dashboard(db: Session = Depends(get_db)):
    sources: dict[str, Any] = {}

    try:
        lockers = _runtime_lockers_summary(db)
    except SQLAlchemyError as exc:
        db.rollback()
        lockers = {"total": 0, "online": 0, "offline": 0, **_source_error(exc)}
    sources["runtime"] = lockers

    try:
        incidents = _incidents_summary(db)
    except SQLAlchemyError as exc:
        db.rollback()
        incidents = {"active": 0, "critical": 0, "deadline_incidents": 0, "failed_domain_events": 0, **_source_error(exc)}
    sources["lifecycle"] = incidents

    try:
        pickups = _pickup_pending_summary(db)
    except SQLAlchemyError as exc:
        db.rollback()
        pickups = {"pending": 0, "overdue": 0, **_source_error(exc)}
    sources["pickup"] = pickups

    degraded_sources = [
        name for name, payload in sources.items()
        if payload.get("status") not in {"ok", None}
    ]

    return {
        "status": "degraded" if degraded_sources else "ok",
        "service": "noc-dashboard",
        "lockers_total": int(lockers.get("total") or 0),
        "lockers_online": int(lockers.get("online") or 0),
        "lockers_offline": int(lockers.get("offline") or 0),
        "incidents_active": int(incidents.get("active") or 0),
        "incidents_critical": int(incidents.get("critical") or 0),
        "pickups_pending": int(pickups.get("pending") or 0),
        "pickups_overdue": int(pickups.get("overdue") or 0),
        "sources": sources,
        "degraded_sources": degraded_sources,
        "last_updated": _now_iso(),
    }


@router.post("/incident/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str):
    return {"status": "acknowledged", "incident_id": incident_id}


@router.post("/incident/fake")
async def create_fake_incident(db: Session = Depends(get_db)):
    now = _now()
    incident_id = f"INC-{now.strftime('%Y%m%d%H%M%S')}"

    event = DomainEvent(
        event_key=f"noc.fake_incident:{incident_id}",
        aggregate_type="noc_incident",
        aggregate_id=incident_id,
        event_name="noc.fake_incident.created",
        event_version=1,
        status=EventStatus.FAILED,
        payload={
            "incident_id": incident_id,
            "severity": "medium",
            "source": "noc.fake",
            "message": "Incidente fake criado para teste do NOC.",
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(event)
    db.commit()

    return {
        "incident_id": incident_id,
        "status": "created",
        "severity": "medium",
        "event_key": event.event_key,
    }
