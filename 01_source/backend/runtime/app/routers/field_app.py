from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.slot_topology import get_valid_slot_ids
from app.core.constants.slot_states import is_slot_available

router = APIRouter(prefix="/api/v1/field", tags=["App Campo"])


class ChecklistItem(BaseModel):
    locker_id: str
    task: str
    status: str  # pending/completed
    timestamp: Optional[str] = None


def _build_error(
    *,
    err_type: str,
    message: str,
    retryable: bool,
    **extra,
) -> dict:
    detail = {
        "type": err_type,
        "message": message,
        "retryable": retryable,
    }
    if extra:
        detail.update(extra)
    return detail


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bootstrap_slots_if_needed(conn, machine_id: str, slot_ids: list[int]) -> None:
    created = 0
    now = _now_iso()
    for slot in slot_ids:
        cur = conn.execute(
            "SELECT 1 FROM door_state WHERE machine_id=? AND door_id=?",
            (machine_id, slot),
        )
        if cur.fetchone() is not None:
            continue

        conn.execute(
            """
            INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(machine_id, door_id) DO NOTHING
            """,
            (machine_id, slot, "AVAILABLE", None, now),
        )
        created += 1

    if created:
        conn.commit()


def _derive_status(slot_states: list[str]) -> str:
    states = {state.upper() for state in slot_states}
    if states.intersection({"FAULT", "BLOCKED"}):
        return "degraded"
    if "MAINTENANCE" in states:
        return "maintenance"
    return "operational"


@router.get("/health")
async def health():
    return {"status": "ok", "service": "field-app"}


@router.post("/checklist")
async def create_checklist(item: ChecklistItem):
    # MVP: apenas valida e retorna
    return {"status": "accepted", "item": item}


@router.get("/locker/{locker_id}/status")
async def get_locker_status(locker_id: str):
    locker_ctx = resolve_runtime_locker(locker_id)
    machine_id = locker_ctx["machine_id"]
    slot_ids = get_valid_slot_ids(locker_ctx)

    try:
        conn = get_conn()
        _bootstrap_slots_if_needed(conn, machine_id, slot_ids)

        placeholders = ",".join("?" for _ in slot_ids)
        cur = conn.execute(
            f"""
            SELECT door_id, state
            FROM door_state
            WHERE machine_id=? AND door_id IN ({placeholders})
            ORDER BY door_id
            """,
            (machine_id, *slot_ids),
        )
        rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="FIELD_LOCKER_STATUS_UNAVAILABLE",
                message="Failed to read real locker status from runtime database.",
                retryable=True,
                locker_id=locker_id,
                error=str(exc),
            ),
        ) from exc

    states_by_slot = {int(row["door_id"]): str(row["state"]) for row in rows}
    slot_states = [states_by_slot.get(slot, "AVAILABLE") for slot in slot_ids]
    slots_free = sum(1 for state in slot_states if is_slot_available(state))

    return {
        "locker_id": locker_ctx["locker_id"],
        "machine_id": machine_id,
        "status": _derive_status(slot_states),
        "slots_free": slots_free,
        "slots_total": len(slot_ids),
        "source": "runtime_db",
    }
