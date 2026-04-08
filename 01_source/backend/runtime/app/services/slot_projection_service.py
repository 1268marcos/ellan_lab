# 01_source/backend/runtime/app/services/slot_projection_service.py
# 08/04/2026 - criação do arquivo

from __future__ import annotations

from typing import Dict, List, Any

from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.slot_topology import get_valid_slot_ids
from app.services.catalog_service import (
    _load_sku_catalog,
    _resolve_slot_plan_for_locker,
)


def _load_door_states(machine_id: str) -> Dict[int, dict]:
    """Carrega os estados reais das portas a partir do SQLite."""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT door_id, state, product_id, updated_at
        FROM door_state
        WHERE machine_id = ?
        """,
        (machine_id,),
    ).fetchall()

    return {
        int(row["door_id"]): {
            "state": row["state"],
            "product_id": row["product_id"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def project_slots(
    *,
    x_locker_id: str | None,
) -> List[Dict[str, Any]]:
    """
    Fonte única de verdade dos slots do locker.

    Combina:
    - Topologia do locker
    - Catálogo de SKUs
    - Estado físico real do runtime
    """

    locker_ctx = resolve_runtime_locker(x_locker_id)
    locker_id = locker_ctx["locker_id"]
    machine_id = locker_ctx["machine_id"]

    slot_ids = get_valid_slot_ids(locker_ctx)

    sku_catalog = _load_sku_catalog()
    slot_plan = _resolve_slot_plan_for_locker(
        locker_id=locker_id,
        slot_ids=slot_ids,
        sku_catalog=sku_catalog,
    )

    door_states = _load_door_states(machine_id)

    results: List[Dict[str, Any]] = []

    for slot in sorted(slot_ids):
        state_info = door_states.get(slot, {})

        state = state_info.get("state", "AVAILABLE")
        product_id = state_info.get("product_id")

        sku_id = slot_plan.get(slot)
        sku_item = sku_catalog.get(sku_id) if sku_id else None

        # Regra de negócio: slot sem produto disponível
        if state == "OUT_OF_STOCK":
            sku_id = None
            sku_item = None

        results.append(
            {
                "locker_id": locker_id,
                "machine_id": machine_id,
                "slot": slot,
                "state": state,
                "product_id": product_id,
                "sku_id": sku_id,
                "name": sku_item["name"] if sku_item else None,
                "amount_cents": sku_item["amount_cents"] if sku_item else None,
                "currency": sku_item["currency"] if sku_item else "BRL",
            }
        )

    return results
