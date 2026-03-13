from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/catalog", tags=["catalog"])


SKU_CATALOG = {
    "bolo_laranja_algarve": {
        "name": "Bolo de Laranja do Algarve",
        "amount_cents": 850,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_cenoura_alentejo": {
        "name": "Bolo de Cenoura do Alentejo",
        "amount_cents": 990,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "mini_bolo_milho": {
        "name": "Mini Bolo de Milho (Fubá)",
        "amount_cents": 495,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_rei": {
        "name": "Bolo Rei",
        "amount_cents": 889,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_rainha": {
        "name": "Bolo Rainha",
        "amount_cents": 1099,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
}


DEFAULT_SLOT_PLAN = {
    1: "bolo_laranja_algarve",
    2: "bolo_cenoura_alentejo",
    3: "mini_bolo_milho",
    4: "bolo_rei",
    5: "bolo_rainha",
    6: "bolo_laranja_algarve",
    7: "bolo_cenoura_alentejo",
    8: "mini_bolo_milho",
    9: "bolo_rei",
    10: "bolo_rainha",
    11: "bolo_laranja_algarve",
    12: "bolo_cenoura_alentejo",
    13: "mini_bolo_milho",
    14: "bolo_rei",
    15: "bolo_rainha",
    16: "bolo_laranja_algarve",
    17: "bolo_cenoura_alentejo",
    18: "mini_bolo_milho",
    19: "bolo_rei",
    20: "bolo_rainha",
    21: "bolo_laranja_algarve",
    22: "bolo_cenoura_alentejo",
    23: "mini_bolo_milho",
    24: "bolo_rei",
}


# -------------------------------------------------------------------
# Sobrescritas por locker
# Pode começar vazio e crescer conforme forem entrando unidades reais.
# -------------------------------------------------------------------
LOCKER_SLOT_PLANS = {
    # Exemplo:
    # "PT-MAIA-CENTRO-LK-001": {
    #     1: "bolo_rei",
    #     2: "bolo_rainha",
    #     3: "mini_bolo_milho",
    # }
    "PT-MAIA-CENTRO-LK-001": {
         1: "bolo_cenoura_alentejo",
         2: "bolo_laranja_algarve",
         3: "bolo_rei",
         4: "bolo_rainha",
         5: "bolo_laranja_algarve",
         6: "bolo_laranja_algarve",
         7: "bolo_laranja_algarve",
         8: "bolo_rainha",
         9: "mini_bolo_milho",
         10: "bolo_cenoura_alentejo",
         11: "mini_bolo_milho",
         12: "bolo_rei",
         13: "bolo_rainha",
         14: "bolo_rainha",
         15: "bolo_cenoura_alentejo",
         16: "bolo_cenoura_alentejo",
         17: "mini_bolo_milho",
         18: "bolo_laranja_algarve",
         19: "bolo_rei",
         20: "mini_bolo_milho",
         21: "bolo_cenoura_alentejo",
         22: "mini_bolo_milho",
         23: "bolo_rei",
         24: "bolo_rei",
    },
    "PT-GUIMARAES-AZUREM-LK-001": {
         1: "mini_bolo_milho",
         2: "bolo_laranja_algarve",
         3: "bolo_cenoura_alentejo",
         4: "bolo_rei",
         5: "bolo_rei",
         6: "bolo_cenoura_alentejo",
         7: "bolo_rainha",
         8: "bolo_rainha",
         9: "bolo_rei",
         10: "bolo_cenoura_alentejo",
         11: "bolo_rei",
         12: "mini_bolo_milho",
         13: "bolo_cenoura_alentejo",
         14: "mini_bolo_milho",
         15: "bolo_rei",
         16: "bolo_cenoura_alentejo",
         17: "mini_bolo_milho",
         18: "bolo_laranja_algarve",
         19: "bolo_rainha",
         20: "bolo_laranja_algarve",
         21: "bolo_laranja_algarve",
         22: "bolo_laranja_algarve",
         23: "bolo_rainha",
         24: "mini_bolo_milho",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_machine_id() -> str:
    import os
    return os.getenv("MACHINE_ID", "CACIFO-PT-001")


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
        "currency": item.get("currency", "EUR"),
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
        "currency": item.get("currency", "EUR") if item else "EUR",
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