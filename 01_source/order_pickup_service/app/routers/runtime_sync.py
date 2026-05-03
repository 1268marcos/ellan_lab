"""OPS: sincronização de slots runtime → Postgres central."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import engine, get_db
from app.services import runtime_slot_sync_service as rss

router = APIRouter(
    prefix="/ops/runtime-sync",
    tags=["ops-runtime-sync"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

_write_dep = Depends(require_user_roles(allowed_roles={"admin_operacao"}))


def _require_pg() -> None:
    if engine.dialect.name != "postgresql":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"type": "RUNTIME_SYNC_PG_ONLY", "message": "Sincronização de slots suportada apenas em PostgreSQL."},
        )


@router.get("/status")
def get_runtime_sync_status(db: Session = Depends(get_db)):
    _require_pg()
    return rss.fetch_queue_status(db)


@router.get("/divergences")
def get_runtime_sync_divergences(db: Session = Depends(get_db)):
    _require_pg()
    return {"items": rss.divergences_report(db)}


@router.post("/run/{locker_id}", dependencies=[_write_dep])
def post_runtime_sync_run(locker_id: str = Path(..., min_length=1), db: Session = Depends(get_db)):
    _require_pg()
    lid = str(locker_id).strip().upper()
    r = db.execute(text("SELECT region FROM lockers WHERE id = :id LIMIT 1"), {"id": lid}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": lid})
    region = str(r.get("region") or "").strip() or None
    return rss.sync_locker_slots_from_runtime(db, lid, region=region)


@router.post("/reconcile-all", dependencies=[_write_dep])
def post_runtime_sync_reconcile_all(db: Session = Depends(get_db)):
    _require_pg()
    return rss.sync_all_active_lockers(db)


@router.post("/retry/{queue_id}", dependencies=[_write_dep])
def post_runtime_sync_retry_queue(queue_id: str = Path(..., min_length=1), db: Session = Depends(get_db)):
    _require_pg()
    qid = str(queue_id).strip()
    try:
        return rss.retry_runtime_sync_queue_item_by_id(db, qid)
    except ValueError as exc:
        msg = str(exc)
        if msg == "QUEUE_ITEM_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"type": msg, "queue_id": qid}) from exc
        if msg == "ALREADY_SUCCESS":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": msg, "queue_id": qid}) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"type": "BAD_REQUEST", "message": msg}) from exc
