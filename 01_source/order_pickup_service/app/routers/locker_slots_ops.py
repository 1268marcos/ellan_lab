"""OPS: locker_slot_configs + locker_slots (leitura e force-release admin)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db

router = APIRouter(
    prefix="/locker",
    tags=["locker-slots-ops"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao"}))],
)


@router.get("/slots/config")
def get_locker_slot_configs(locker_id: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM lockers WHERE id = :id LIMIT 1"), {"id": locker_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": locker_id})
    rows = db.execute(
        text(
            """
            SELECT id, locker_id, slot_size, slot_count, COALESCE(available_count, slot_count) AS available_count,
                   width_mm, height_mm, depth_mm
            FROM locker_slot_configs
            WHERE locker_id = :locker_id
            ORDER BY slot_size
            """
        ),
        {"locker_id": locker_id},
    ).mappings().all()
    return {"locker_id": locker_id, "configs": [dict(r) for r in rows]}


@router.get("/slots/status")
def get_locker_slots_status(locker_id: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM lockers WHERE id = :id LIMIT 1"), {"id": locker_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": locker_id})
    rows = db.execute(
        text(
            """
            SELECT id, locker_id, slot_label, slot_size, status, current_allocation_id,
                   current_delivery_id, fault_code
            FROM locker_slots
            WHERE locker_id = :locker_id
            ORDER BY slot_label
            """
        ),
        {"locker_id": locker_id},
    ).mappings().all()
    return {"locker_id": locker_id, "slots": [dict(r) for r in rows]}


@router.post("/slots/{slot}/force-release", status_code=status.HTTP_200_OK)
def post_force_release_slot(
    slot: str,
    locker_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    lk = db.execute(text("SELECT id FROM lockers WHERE id = :id LIMIT 1"), {"id": locker_id}).mappings().first()
    if not lk:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": locker_id})
    slot_row = db.execute(
        text(
            """
            SELECT id, slot_label, status, current_allocation_id
            FROM locker_slots
            WHERE locker_id = :locker_id AND (id = :slot OR slot_label = :slot)
            LIMIT 1
            """
        ),
        {"locker_id": locker_id, "slot": slot},
    ).mappings().first()
    if not slot_row:
        raise HTTPException(status_code=404, detail={"type": "SLOT_NOT_FOUND", "message": slot, "locker_id": locker_id})

    sid = str(slot_row["id"])
    alloc_id = slot_row.get("current_allocation_id")
    st = str(slot_row.get("status") or "").upper()
    if st == "AVAILABLE" and not alloc_id:
        return {"ok": True, "idempotent": True, "slot_id": sid, "slot_label": str(slot_row["slot_label"]), "message": "Slot já livre."}

    now = datetime.now(timezone.utc)
    if alloc_id:
        db.execute(
            text(
                """
                UPDATE allocations
                SET state = 'RELEASED', released_at = :now, updated_at = :now,
                    release_reason = 'OPS_FORCE_RELEASE'
                WHERE id = :aid
                  AND state::text NOT IN ('PICKED_UP','RELEASED','CANCELLED','EXPIRED')
                """
            ),
            {"aid": str(alloc_id), "now": now},
        )
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = 'AVAILABLE',
                occupied_since = NULL,
                current_allocation_id = NULL,
                current_delivery_id = NULL,
                current_rental_id = NULL,
                updated_at = :now
            WHERE id = :sid
            """
        ),
        {"sid": sid, "now": now},
    )
    db.commit()
    return {
        "ok": True,
        "idempotent": False,
        "slot_id": sid,
        "slot_label": str(slot_row["slot_label"]),
        "previous_status": st,
        "released_allocation_id": str(alloc_id) if alloc_id else None,
    }
