# 01_source/backend_sp/app/routers/dev_allocations.py
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.db import get_conn

router = APIRouter(prefix="/dev/allocations", tags=["dev-allocations"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _machine_id() -> str:
    import os
    return os.getenv("MACHINE_ID", "CACIFO-SP-001")


def _raise(status: int, *, err_type: str, message: str, retryable: bool, **extra):
    detail = {"type": err_type, "message": message, "retryable": retryable}
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=status, detail=detail)


def _door_state_get(conn, machine_id: str, door_id: int) -> Optional[str]:
    cur = conn.execute(
        "SELECT state FROM door_state WHERE machine_id=? AND door_id=?",
        (machine_id, door_id),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _door_state_upsert(conn, machine_id: str, door_id: int, state: str, product_id: Optional[str] = None) -> None:
    conn.execute(
        """
        INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET state=excluded.state, product_id=excluded.product_id, updated_at=excluded.updated_at
        """,
        (machine_id, door_id, state, product_id, _now_iso()),
    )


class ReleaseOrphanAllocationsIn(BaseModel):
    locker_id: Optional[str] = Field(
        default=None,
        description="Locker alvo. Se omitido, usa MACHINE_ID do backend.",
    )
    slots: list[int] = Field(
        default_factory=list,
        description="Lista opcional de slots para limpeza. Vazio = todos os slots do locker.",
    )
    include_committed: bool = Field(
        default=True,
        description="Também libera allocations COMMITTED, além de RESERVED.",
    )


@router.post("/release-orphans")
def release_orphan_allocations(payload: ReleaseOrphanAllocationsIn, request: Request):
    machine_id = (payload.locker_id or "").strip() or _machine_id()

    try:
        conn = get_conn()

        target_states = ["RESERVED"]
        if payload.include_committed:
            target_states.append("COMMITTED")

        params = [machine_id, *target_states]

        sql = f"""
            SELECT allocation_id, door_id, state, expires_at, sale_id, request_id
            FROM allocations
            WHERE machine_id=?
              AND state IN ({",".join("?" for _ in target_states)})
        """

        if payload.slots:
            slot_placeholders = ",".join("?" for _ in payload.slots)
            sql += f" AND door_id IN ({slot_placeholders})"
            params.extend(payload.slots)

        sql += " ORDER BY door_id, created_at"

        cur = conn.execute(sql, tuple(params))
        rows = cur.fetchall()

        inspected = 0
        released_allocation_ids: list[str] = []
        slot_resets: list[dict] = []

        for row in rows:
            inspected += 1
            allocation_id = row["allocation_id"]
            door_id = int(row["door_id"])
            prev_state = row["state"]

            conn.execute(
                """
                UPDATE allocations
                SET state='RELEASED', request_id=COALESCE(request_id, 'dev-release-orphans')
                WHERE allocation_id=? AND machine_id=?
                """,
                (allocation_id, machine_id),
            )

            current_door_state = _door_state_get(conn, machine_id, door_id)
            if current_door_state == "RESERVED":
                _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)
                slot_resets.append(
                    {
                        "slot": door_id,
                        "old_state": current_door_state,
                        "new_state": "AVAILABLE",
                    }
                )
            else:
                slot_resets.append(
                    {
                        "slot": door_id,
                        "old_state": current_door_state,
                        "new_state": current_door_state,
                    }
                )

            released_allocation_ids.append(allocation_id)

        conn.commit()

        return {
            "ok": True,
            "machine_id": machine_id,
            "locker_id": machine_id,
            "endpoint": str(request.url.path),
            "inspected": inspected,
            "released_count": len(released_allocation_ids),
            "released_allocation_ids": released_allocation_ids,
            "slot_resets": slot_resets,
            "message": (
                "Limpeza DEV concluída. Allocations órfãs ativas foram marcadas como RELEASED "
                "e slots RESERVED foram devolvidos para AVAILABLE."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DEV_RELEASE_ORPHANS_FAILED",
            message=str(e),
            retryable=True,
            machine_id=machine_id,
            endpoint=str(request.url.path),
        )