# 01_source/backend_pt/app/routers/catalog.py
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/catalog", tags=["catalog"])


SKU_CATALOG = {
    "cookie_laranja_algarve": {
        "name": "Cookie de Laranja do Algarve",
        "amount_cents": 850,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_cenoura_alentejo": {
        "name": "Cookie de Cenoura do Alentejo",
        "amount_cents": 990,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "mini_cookie_milho": {
        "name": "Mini Cookie de Milho (Fubá)",
        "amount_cents": 495,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_rei": {
        "name": "Cookie Rei",
        "amount_cents": 889,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_rainha": {
        "name": "Cookie Rainha",
        "amount_cents": 1099,
        "currency": "EUR",
        "imageURL": "",
        "is_active": True,
    },
}


DEFAULT_SLOT_PLAN = {
    1: "cookie_laranja_algarve",
    2: "cookie_cenoura_alentejo",
    3: "mini_cookie_milho",
    4: "cookie_rei",
    5: "cookie_rainha",
    6: "cookie_laranja_algarve",
    7: "cookie_cenoura_alentejo",
    8: "mini_cookie_milho",
    9: "cookie_rei",
    10: "cookie_rainha",
    11: "cookie_laranja_algarve",
    12: "cookie_cenoura_alentejo",
    13: "mini_cookie_milho",
    14: "cookie_rei",
    15: "cookie_rainha",
    16: "cookie_laranja_algarve",
    17: "cookie_cenoura_alentejo",
    18: "mini_cookie_milho",
    19: "cookie_rei",
    20: "cookie_rainha",
    21: "cookie_laranja_algarve",
    22: "cookie_cenoura_alentejo",
    23: "mini_cookie_milho",
    24: "cookie_rei",
}


# -------------------------------------------------------------------
# Sobrescritas por locker
# Pode começar vazio e crescer conforme forem entrando unidades reais.
# -------------------------------------------------------------------
LOCKER_SLOT_PLANS = {
    # Exemplo:
    # "PT-MAIA-CENTRO-LK-001": {
    #     1: "cookie_rei",
    #     2: "cookie_rainha",
    #     3: "mini_cookie_milho",
    # }
    "PT-MAIA-CENTRO-LK-001": {
         1: "cookie_cenoura_alentejo",
         2: "cookie_laranja_algarve",
         3: "cookie_rei",
         4: "cookie_rainha",
         5: "cookie_laranja_algarve",
         6: "cookie_laranja_algarve",
         7: "cookie_laranja_algarve",
         8: "cookie_rainha",
         9: "mini_cookie_milho",
         10: "cookie_cenoura_alentejo",
         11: "mini_cookie_milho",
         12: "cookie_rei",
         13: "cookie_rainha",
         14: "cookie_rainha",
         15: "cookie_cenoura_alentejo",
         16: "cookie_cenoura_alentejo",
         17: "mini_cookie_milho",
         18: "cookie_laranja_algarve",
         19: "cookie_rei",
         20: "mini_cookie_milho",
         21: "cookie_cenoura_alentejo",
         22: "mini_cookie_milho",
         23: "cookie_rei",
         24: "cookie_rei",
    },
    "PT-GUIMARAES-AZUREM-LK-001": {
         1: "mini_cookie_milho",
         2: "cookie_laranja_algarve",
         3: "cookie_cenoura_alentejo",
         4: "cookie_rei",
         5: "cookie_rei",
         6: "cookie_cenoura_alentejo",
         7: "cookie_rainha",
         8: "cookie_rainha",
         9: "cookie_rei",
         10: "cookie_cenoura_alentejo",
         11: "cookie_rei",
         12: "mini_cookie_milho",
         13: "cookie_cenoura_alentejo",
         14: "mini_cookie_milho",
         15: "cookie_rei",
         16: "cookie_cenoura_alentejo",
         17: "mini_cookie_milho",
         18: "cookie_laranja_algarve",
         19: "cookie_rainha",
         20: "cookie_laranja_algarve",
         21: "cookie_laranja_algarve",
         22: "cookie_laranja_algarve",
         23: "cookie_rainha",
         24: "mini_cookie_milho",
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