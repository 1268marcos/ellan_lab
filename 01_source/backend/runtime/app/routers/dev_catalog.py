from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.slot_topology import ensure_valid_slot
from app.services.catalog_service import list_catalog_slots, list_catalog_skus

router = APIRouter(prefix="/dev/catalog", tags=["dev-catalog"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assert_dev_access(x_internal_token: str | None) -> None:
    expected = str(settings.internal_token or "").strip()
    if not expected:
        return
    if str(x_internal_token or "").strip() != expected:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "DEV_CATALOG_FORBIDDEN",
                "message": "X-Internal-Token inválido para operação de catálogo DEV.",
                "retryable": False,
            },
        )


class SlotAllocationIn(BaseModel):
    slot: int = Field(..., gt=0)
    sku_id: str = Field(..., min_length=1, max_length=255)


class SlotAllocationBatchIn(BaseModel):
    allocations: list[SlotAllocationIn] = Field(default_factory=list)


@router.get("/slot-overrides")
def list_slot_overrides(
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_dev_access(x_internal_token)
    locker_ctx = resolve_runtime_locker(x_locker_id)
    machine_id = locker_ctx["machine_id"]

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT door_id, sku_id, updated_at
        FROM catalog_slot_overrides
        WHERE machine_id = ?
        ORDER BY door_id
        """,
        (machine_id,),
    ).fetchall()

    return {
        "ok": True,
        "locker_id": locker_ctx["locker_id"],
        "machine_id": machine_id,
        "items": [
            {
                "slot": int(row["door_id"]),
                "sku_id": str(row["sku_id"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ],
    }


@router.post("/slots/{slot}")
def set_slot_allocation(
    slot: int,
    payload: SlotAllocationIn,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_dev_access(x_internal_token)
    locker_ctx = resolve_runtime_locker(x_locker_id)
    ensure_valid_slot(locker_ctx, slot)

    if int(payload.slot) != int(slot):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "SLOT_MISMATCH",
                "message": "slot do path e slot do payload não conferem.",
                "retryable": False,
                "path_slot": int(slot),
                "payload_slot": int(payload.slot),
            },
        )

    sku_ids = {item.sku_id for item in list_catalog_skus(x_locker_id=locker_ctx["locker_id"])}
    if payload.sku_id not in sku_ids:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "SKU_NOT_FOUND",
                "message": "sku_id não encontrado no catálogo ativo do runtime.",
                "retryable": False,
                "sku_id": payload.sku_id,
            },
        )

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO catalog_slot_overrides(machine_id, door_id, sku_id, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET sku_id=excluded.sku_id, updated_at=excluded.updated_at
        """,
        (locker_ctx["machine_id"], int(slot), payload.sku_id, _now_iso()),
    )
    conn.commit()

    return {
        "ok": True,
        "locker_id": locker_ctx["locker_id"],
        "machine_id": locker_ctx["machine_id"],
        "slot": int(slot),
        "sku_id": payload.sku_id,
    }


@router.post("/slot-overrides/batch")
def set_slot_allocation_batch(
    payload: SlotAllocationBatchIn,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_dev_access(x_internal_token)
    locker_ctx = resolve_runtime_locker(x_locker_id)

    sku_ids = {item.sku_id for item in list_catalog_skus(x_locker_id=locker_ctx["locker_id"])}
    conn = get_conn()
    updated = []

    for item in payload.allocations:
        ensure_valid_slot(locker_ctx, int(item.slot))
        if item.sku_id not in sku_ids:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "SKU_NOT_FOUND",
                    "message": "sku_id não encontrado no catálogo ativo do runtime.",
                    "retryable": False,
                    "sku_id": item.sku_id,
                    "slot": int(item.slot),
                },
            )

        conn.execute(
            """
            INSERT INTO catalog_slot_overrides(machine_id, door_id, sku_id, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(machine_id, door_id)
            DO UPDATE SET sku_id=excluded.sku_id, updated_at=excluded.updated_at
            """,
            (locker_ctx["machine_id"], int(item.slot), item.sku_id, _now_iso()),
        )
        updated.append({"slot": int(item.slot), "sku_id": item.sku_id})

    conn.commit()

    return {
        "ok": True,
        "locker_id": locker_ctx["locker_id"],
        "machine_id": locker_ctx["machine_id"],
        "updated_count": len(updated),
        "items": updated,
    }


@router.delete("/slots/{slot}")
def clear_slot_allocation(
    slot: int,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_dev_access(x_internal_token)
    locker_ctx = resolve_runtime_locker(x_locker_id)
    ensure_valid_slot(locker_ctx, slot)

    conn = get_conn()
    res = conn.execute(
        """
        DELETE FROM catalog_slot_overrides
        WHERE machine_id = ? AND door_id = ?
        """,
        (locker_ctx["machine_id"], int(slot)),
    )
    conn.commit()

    return {
        "ok": True,
        "locker_id": locker_ctx["locker_id"],
        "machine_id": locker_ctx["machine_id"],
        "slot": int(slot),
        "deleted": int(res.rowcount),
    }


@router.get("/slots")
def list_slots_with_catalog(
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_dev_access(x_internal_token)
    locker_ctx = resolve_runtime_locker(x_locker_id)

    slots = list_catalog_slots(x_locker_id=locker_ctx["locker_id"])
    skus = list_catalog_skus(x_locker_id=locker_ctx["locker_id"])

    return {
        "ok": True,
        "locker_id": locker_ctx["locker_id"],
        "machine_id": locker_ctx["machine_id"],
        "slots": [item.model_dump() for item in slots],
        "skus": [item.model_dump() for item in skus],
    }
