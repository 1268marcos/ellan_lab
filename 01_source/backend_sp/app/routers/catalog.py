from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/catalog", tags=["catalog"])


SKU_CATALOG = {
    "bolo_laranja": {
        "name": "Bolo de Laranja",
        "amount_cents": 4850,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_cenoura": {
        "name": "Bolo de Cenoura",
        "amount_cents": 4990,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "mini_bolo_iogurte": {
        "name": "Mini Bolo de Iogurte",
        "amount_cents": 4495,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_especial": {
        "name": "Bolo Especial",
        "amount_cents": 4889,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_canetinha": {
        "name": "Bolo Canetinha",
        "amount_cents": 11099,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
}


DEFAULT_SLOT_PLAN = {
    1: "bolo_laranja",
    2: "bolo_cenoura",
    3: "mini_bolo_iogurte",
    4: "bolo_especial",
    5: "bolo_canetinha",
    6: "bolo_laranja",
    7: "bolo_cenoura",
    8: "mini_bolo_iogurte",
    9: "bolo_especial",
    10: "bolo_canetinha",
    11: "bolo_laranja",
    12: "bolo_cenoura",
    13: "mini_bolo_iogurte",
    14: "bolo_especial",
    15: "bolo_canetinha",
    16: "bolo_laranja",
    17: "bolo_cenoura",
    18: "mini_bolo_iogurte",
    19: "bolo_especial",
    20: "bolo_canetinha",
    21: "bolo_laranja",
    22: "bolo_cenoura",
    23: "mini_bolo_iogurte",
    24: "bolo_especial",
}


# -------------------------------------------------------------------
# Sobrescritas por locker
# Pode começar vazio e crescer conforme forem entrando unidades reais.
# -------------------------------------------------------------------
LOCKER_SLOT_PLANS = {
    # Exemplo:
    # "SP-OSASCO-CENTRO-LK-001": {
    #     1: "bolo_especial",
    #     2: "bolo_canetinha",
    #     3: "mini_bolo_iogurte",
    # }
    "SP-OSASCO-CENTRO-LK-001": {
        1: "bolo_laranja",
        2: "bolo_laranja",
        3: "bolo_cenoura",
        4: "bolo_especial",
        5: "mini_bolo_iogurte",
        6: "bolo_cenoura",
        7: "bolo_canetinha",
        8: "mini_bolo_iogurte",
        9: "bolo_especial",
        10: "bolo_canetinha",
        11: "bolo_especial",
        12: "bolo_canetinha",
        13: "bolo_laranja",
        14: "bolo_cenoura",
        15: "mini_bolo_iogurte",
        16: "bolo_laranja",
        17: "bolo_cenoura",
        18: "mini_bolo_iogurte",
        19: "bolo_especial",
        20: "bolo_canetinha",
        21: "bolo_laranja",
        22: "bolo_cenoura",
        23: "mini_bolo_iogurte",
        24: "bolo_especial",
    },
    "SP-CARAPICUIBA-JDMARILU-LK-001": {
        1: "bolo_cenoura",
        2: "bolo_especial",
        3: "mini_bolo_iogurte",
        4: "mini_bolo_iogurte",
        5: "bolo_cenoura",
        6: "bolo_canetinha",
        7: "mini_bolo_iogurte",
        8: "bolo_especial",
        9: "bolo_canetinha",
        10: "bolo_especial",
        11: "bolo_canetinha",
        12: "bolo_laranja",
        13: "bolo_cenoura",
        14: "mini_bolo_iogurte",
        15: "bolo_laranja",
        16: "bolo_cenoura",
        17: "mini_bolo_iogurte",
        18: "bolo_especial",
        19: "bolo_canetinha",
        20: "bolo_laranja",
        21: "bolo_cenoura",
        22: "bolo_laranja",
        23: "bolo_especial",
        24: "bolo_laranja",
    },

}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_machine_id() -> str:
    import os
    return os.getenv("MACHINE_ID", "CACIFO-SP-001")


def _resolve_machine_id(x_locker_id: str | None) -> str:
    explicit = (x_locker_id or "").strip()
    if explicit:
        return explicit
    return _default_machine_id()


def _resolve_slot_plan(machine_id: str) -> dict[int, str]:
    """
    Regra:
    - usa plano específico do locker se existir
    - senão usa plano default regional
    """
    locker_plan = LOCKER_SLOT_PLANS.get(machine_id)
    if locker_plan:
        merged = dict(DEFAULT_SLOT_PLAN)
        merged.update(locker_plan)
        return merged
    return dict(DEFAULT_SLOT_PLAN)


def _sku_out(sku_id: str, item: dict, machine_id: Optional[str] = None) -> dict:
    return {
        "locker_id": machine_id,
        "sku_id": sku_id,
        "name": item["name"],
        "amount_cents": int(item["amount_cents"]),
        "currency": item.get("currency", "BRL"),
        "imageURL": item.get("imageURL", ""),
        "is_active": bool(item.get("is_active", True)),
        "updated_at": _now_iso(),
    }


def _slot_item_out(slot: int, sku_id: Optional[str], item: Optional[dict], machine_id: str) -> dict:
    return {
        "locker_id": machine_id,
        "slot": slot,
        "sku_id": sku_id,
        "name": item["name"] if item else None,
        "amount_cents": int(item["amount_cents"]) if item else None,
        "currency": item.get("currency", "BRL") if item else "BRL",
        "imageURL": item.get("imageURL", "") if item else "",
        "is_active": bool(item.get("is_active", True)) if item else False,
        "updated_at": _now_iso(),
    }


@router.get("/skus")
def list_skus(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    machine_id = _resolve_machine_id(x_locker_id)

    return [
        _sku_out(sku_id, item, machine_id)
        for sku_id, item in SKU_CATALOG.items()
        if item.get("is_active", True)
    ]


@router.get("/skus/{sku_id}")
def get_sku(
    sku_id: str,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    machine_id = _resolve_machine_id(x_locker_id)

    item = SKU_CATALOG.get(sku_id)
    if not item or not item.get("is_active", True):
        raise HTTPException(
            status_code=404,
            detail={
                "type": "SKU_NOT_FOUND",
                "message": "sku not found or inactive",
                "retryable": False,
                "sku_id": sku_id,
                "locker_id": machine_id,
            },
        )

    return _sku_out(sku_id, item, machine_id)


@router.get("/slots")
def list_catalog_slots(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    machine_id = _resolve_machine_id(x_locker_id)
    slot_plan = _resolve_slot_plan(machine_id)

    items = []

    for slot in range(1, 25):
        sku_id = slot_plan.get(slot)
        item = SKU_CATALOG.get(sku_id) if sku_id else None

        items.append(_slot_item_out(slot, sku_id, item, machine_id))

    return items