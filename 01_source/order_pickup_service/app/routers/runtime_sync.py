"""OPS: sincronização de slots runtime → Postgres central."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
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


class OpsRuntimeOverrideBody(BaseModel):
    locker_id: str = Field(..., min_length=1)
    slot_label: str = Field(..., min_length=1)
    target_status: str = Field(..., min_length=1)
    reason: str = Field("", max_length=4000)


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


@router.get("/validate/{locker_id}")
def get_runtime_sync_validate(locker_id: str = Path(..., min_length=1), db: Session = Depends(get_db)):
    _require_pg()
    lid = str(locker_id).strip().upper()
    out = rss.validate_sync_consistency(db, lid)
    if not out.get("ok"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out)
    return out


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


@router.post("/override", dependencies=[_write_dep])
def post_ops_runtime_override(body: OpsRuntimeOverrideBody, db: Session = Depends(get_db)):
    _require_pg()
    out = rss.apply_ops_runtime_override_push_runtime(
        db,
        locker_id=body.locker_id,
        slot_label=body.slot_label,
        target_status=body.target_status,
        reason=body.reason,
    )
    if out.get("ok"):
        return out
    err = str(out.get("error") or "FAILED")
    if err == "LOCKER_NOT_FOUND":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out)
    if err == "SLOT_NOT_FOUND":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out)
    if err == "INVALID_TARGET_STATUS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=out)
    if err == "RUNTIME_PUSH_FAILED":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=out)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=out)


@router.get("/override-history")
def get_ops_runtime_override_history(limit: int = Query(200, ge=1, le=500), db: Session = Depends(get_db)):
    _require_pg()
    return {"items": rss.list_override_history(db, limit=limit)}
