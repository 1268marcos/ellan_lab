# 01_source/backend/runtime/app/routers/locker_state.py
"""
Objetivo

Listar estado dos slots de acordo com a topologia real do locker.
Deve criar/projetar apenas os slots realmente válidos para aquele locker.

Deve refletir o estado real do locker e não inventar 24 portas fixas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.slot_topology import get_valid_slot_ids, ensure_valid_slot
from app.core.constants.slot_states import SLOT_STATES, SlotState

router = APIRouter(prefix="/locker", tags=["locker"])


class SlotView(BaseModel):
    slot: int
    state: SlotState
    product_id: Optional[str] = None
    updated_at: str


class SetSlotStateIn(BaseModel):
    state: SlotState
    product_id: Optional[str] = None


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


def _get_slot(conn, machine_id: str, slot: int) -> Optional[dict]:
    cur = conn.execute(
        "SELECT state, product_id, updated_at FROM door_state WHERE machine_id=? AND door_id=?",
        (machine_id, slot),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "state": row[0],
        "product_id": row[1],
        "updated_at": row[2],
    }


def _upsert_slot(
    conn,
    machine_id: str,
    slot: int,
    state: str,
    product_id: Optional[str],
) -> dict:
    if state not in SLOT_STATES:
        raise HTTPException(
            status_code=400,
            detail=_build_error(
                err_type="INVALID_SLOT_STATE",
                message="Slot state is invalid.",
                retryable=False,
                state=state,
                allowed_states=list(SLOT_STATES),
            ),
        )

    now = _now_iso()
    conn.execute(
        """
        INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET state=excluded.state, product_id=excluded.product_id, updated_at=excluded.updated_at
        """,
        (machine_id, slot, state, product_id, now),
    )
    conn.commit()

    return {
        "slot": slot,
        "state": state,
        "product_id": product_id,
        "updated_at": now,
    }


def _bootstrap_slots_if_needed(conn, machine_id: str, slot_ids: list[int]) -> None:
    """
    Cria apenas os slots válidos da topologia do locker.
    Não assume mais range fixo 1..24.
    """
    created = 0

    for slot in slot_ids:
        if _get_slot(conn, machine_id, slot) is None:
            conn.execute(
                """
                INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(machine_id, door_id) DO NOTHING
                """,
                (machine_id, slot, "AVAILABLE", None, _now_iso()),
            )
            created += 1

    if created > 0:
        conn.commit()


@router.get("/slots", response_model=List[SlotView])
def list_slots(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    locker_ctx = resolve_runtime_locker(x_locker_id)
    machine_id = locker_ctx["machine_id"]
    slot_ids = get_valid_slot_ids(locker_ctx)

    try:
        conn = get_conn()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_CONNECTION_FAILED",
                message="Failed to connect to runtime database.",
                retryable=True,
                service="backend_runtime",
                endpoint=str(request.url.path),
                locker_id=locker_ctx["locker_id"],
                machine_id=machine_id,
                error=str(exc),
            ),
        ) from exc

    try:
        _bootstrap_slots_if_needed(conn, machine_id, slot_ids)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_BOOTSTRAP_FAILED",
                message="Failed to bootstrap locker slot state.",
                retryable=True,
                service="backend_runtime",
                endpoint=str(request.url.path),
                locker_id=locker_ctx["locker_id"],
                machine_id=machine_id,
                slot_ids=slot_ids,
                error=str(exc),
            ),
        ) from exc

    try:
        out: list[SlotView] = []

        for slot in slot_ids:
            row = _get_slot(conn, machine_id, slot)
            if row is None:
                row = _upsert_slot(conn, machine_id, slot, "AVAILABLE", None)

            out.append(
                SlotView(
                    slot=int(slot),
                    state=row["state"],
                    product_id=row["product_id"],
                    updated_at=row["updated_at"],
                )
            )

        return out

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_QUERY_FAILED",
                message="Failed to query locker slots.",
                retryable=True,
                service="backend_runtime",
                endpoint=str(request.url.path),
                locker_id=locker_ctx["locker_id"],
                machine_id=machine_id,
                error=str(exc),
            ),
        ) from exc


@router.get("/slots/{slot}", response_model=SlotView)
def get_slot(
    slot: int,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    locker_ctx = resolve_runtime_locker(x_locker_id)
    machine_id = locker_ctx["machine_id"]
    ensure_valid_slot(locker_ctx, slot)

    try:
        conn = get_conn()
        row = _get_slot(conn, machine_id, slot)

        if row is None:
            row = _upsert_slot(conn, machine_id, slot, "AVAILABLE", None)

        return SlotView(
            slot=slot,
            state=row["state"],
            product_id=row["product_id"],
            updated_at=row["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_OPERATION_FAILED",
                message="Failed to get slot state.",
                retryable=True,
                service="backend_runtime",
                endpoint=str(request.url.path),
                locker_id=locker_ctx["locker_id"],
                machine_id=machine_id,
                slot=slot,
                error=str(exc),
            ),
        ) from exc


@router.post("/slots/{slot}/set-state")
def set_slot_state(
    slot: int,
    payload: SetSlotStateIn,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    locker_ctx = resolve_runtime_locker(x_locker_id)
    machine_id = locker_ctx["machine_id"]
    ensure_valid_slot(locker_ctx, slot)

    try:
        conn = get_conn()
        prev = _get_slot(conn, machine_id, slot)
        new_row = _upsert_slot(conn, machine_id, slot, payload.state, payload.product_id)

        return {
            "ok": True,
            "service": "backend_runtime",
            "locker_id": locker_ctx["locker_id"],
            "machine_id": machine_id,
            "region": locker_ctx.get("region"),
            "endpoint": str(request.url.path),
            "slot": slot,
            "old_state": prev["state"] if prev else None,
            "state": new_row["state"],
            "product_id": new_row["product_id"],
            "updated_at": new_row["updated_at"],
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_UPDATE_FAILED",
                message="Failed to update slot state.",
                retryable=True,
                service="backend_runtime",
                endpoint=str(request.url.path),
                locker_id=locker_ctx["locker_id"],
                machine_id=machine_id,
                slot=slot,
                desired_state=payload.state,
                error=str(exc),
            ),
        ) from exc
        


"""
Observação importante

Neste momento, o locker_runtime_resolver.py ainda usa fallback:

X-Locker-Id
senão MACHINE_ID
SLOT_IDS_JSON
senão LOCKER_SLOT_COUNT
senão 24

Isso foi intencional para você conseguir subir o runtime sem travar tudo de uma vez.

Mas o destino correto é:

resolve_runtime_locker() -> consulta central -> topologia real do locker

e aí o fallback fixo desaparece.
"""