# 01_source/backend/runtime/app/routers/catalog.py
"""
Objetivo

Transformar em camada transitória:

manter catálogo mock se precisar
mas parar de assumir 24 slots fixos
slot plan deve ser coerente com a topologia do locker
idealmente, depois, migrar SKU e disponibilidade para fonte central/configurável

No início pode continuar mockado, mas:

não deve assumir 24 slots fixos
deve respeitar topologia por locker
depois pode evoluir para catálogo real por locker
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/catalog", tags=["catalog"])


SKU_CATALOG = {
    "cookie_laranja": {
        "name": "Cookie de Laranja",
        "amount_cents": 4850,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_cenoura": {
        "name": "Cookie de Cenoura",
        "amount_cents": 4990,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "mini_cookie_iogurte": {
        "name": "Mini Cookie de Iogurte",
        "amount_cents": 4495,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_especial": {
        "name": "Cookie Especial",
        "amount_cents": 4889,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "cookie_canetinha": {
        "name": "Cookie Canetinha",
        "amount_cents": 11099,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
}


DEFAULT_SLOT_PLAN = {
    1: "cookie_laranja",
    2: "cookie_cenoura",
    3: "mini_cookie_iogurte",
    4: "cookie_especial",
    5: "cookie_canetinha",
    6: "cookie_laranja",
    7: "cookie_cenoura",
    8: "mini_cookie_iogurte",
    9: "cookie_especial",
    10: "cookie_canetinha",
    11: "cookie_laranja",
    12: "cookie_cenoura",
    13: "mini_cookie_iogurte",
    14: "cookie_especial",
    15: "cookie_canetinha",
    16: "cookie_laranja",
    17: "cookie_cenoura",
    18: "mini_cookie_iogurte",
    19: "cookie_especial",
    20: "cookie_canetinha",
    21: "cookie_laranja",
    22: "cookie_cenoura",
    23: "mini_cookie_iogurte",
    24: "cookie_especial",
}


# -------------------------------------------------------------------
# Sobrescritas por locker
# Pode começar vazio e crescer conforme forem entrando unidades reais.
# -------------------------------------------------------------------
LOCKER_SLOT_PLANS = {
    # Exemplo:
    # "SP-OSASCO-CENTRO-LK-001": {
    #     1: "cookie_especial",
    #     2: "cookie_canetinha",
    #     3: "mini_cookie_iogurte",
    # }
    "SP-OSASCO-CENTRO-LK-001": {
        1: "cookie_laranja",
        2: "cookie_laranja",
        3: "cookie_cenoura",
        4: "cookie_especial",
        5: "mini_cookie_iogurte",
        6: "cookie_cenoura",
        7: "cookie_canetinha",
        8: "mini_cookie_iogurte",
        9: "cookie_especial",
        10: "cookie_canetinha",
        11: "cookie_especial",
        12: "cookie_canetinha",
        13: "cookie_laranja",
        14: "cookie_cenoura",
        15: "mini_cookie_iogurte",
        16: "cookie_laranja",
        17: "cookie_cenoura",
        18: "mini_cookie_iogurte",
        19: "cookie_especial",
        20: "cookie_canetinha",
        21: "cookie_laranja",
        22: "cookie_cenoura",
        23: "mini_cookie_iogurte",
        24: "cookie_especial",
    },
    "SP-CARAPICUIBA-JDMARILU-LK-001": {
        1: "cookie_cenoura",
        2: "cookie_especial",
        3: "mini_cookie_iogurte",
        4: "mini_cookie_iogurte",
        5: "cookie_cenoura",
        6: "cookie_canetinha",
        7: "mini_cookie_iogurte",
        8: "cookie_especial",
        9: "cookie_canetinha",
        10: "cookie_especial",
        11: "cookie_canetinha",
        12: "cookie_laranja",
        13: "cookie_cenoura",
        14: "mini_cookie_iogurte",
        15: "cookie_laranja",
        16: "cookie_cenoura",
        17: "mini_cookie_iogurte",
        18: "cookie_especial",
        19: "cookie_canetinha",
        20: "cookie_laranja",
        21: "cookie_cenoura",
        22: "cookie_laranja",
        23: "cookie_especial",
        24: "cookie_laranja",
    },
    "CACIFO-SP-001": {
        1: "cookie_canetinha",
        2: "cookie_especial",
        3: "mini_cookie_iogurte",
        4: "mini_cookie_iogurte",
        5: "cookie_cenoura",
        6: "cookie_cenoura",
        7: "mini_cookie_iogurte",
        8: "cookie_especial",
        9: "cookie_canetinha",
        10: "cookie_especial",
        11: "cookie_laranja",
        12: "cookie_laranja",
        13: "cookie_cenoura",
        14: "mini_cookie_iogurte",
        15: "cookie_laranja",
        16: "cookie_laranja",
        17: "mini_cookie_iogurte",
        18: "cookie_especial",
        19: "cookie_canetinha",
        20: "cookie_laranja",
        21: "cookie_cenoura",
        22: "cookie_laranja",
        23: "cookie_especial",
        24: "mini_cookie_iogurte",
    },
}

# -------------------------------------------------------------------
# Aceitar Lockers dinâmicos
# -------------------------------------------------------------------
KNOWN_LOCKERS = {
    "SP-OSASCO-CENTRO-LK-001",
    "SP-CARAPICUIBA-JDMARILU-LK-001",
    "PT-MAIA-CENTRO-LK-001",
    "PT-GUIMARAES-AZUREM-LK-001",

    # DEV
    "CACIFO-SP-001",
    "CACIFO-PT-001",
}

def validate_locker_id(locker_id: str):
    if locker_id in KNOWN_LOCKERS:
        return

    # fallback seguro (modo DEV)
    if locker_id.startswith("SP-") or locker_id.startswith("PT-") or locker_id.startswith("CACIFO-"):
        return

    raise HTTPException(
        status_code=400,
        detail={
            "type": "LOCKER_NOT_FOUND",
            "message": f"Locker não encontrado: {locker_id}",
            "locker_id": locker_id,
            "retryable": False,
        },
    )


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