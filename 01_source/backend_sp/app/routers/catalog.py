from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter(prefix="/catalog", tags=["catalog"])

SKU_CATALOG = {
    "bolo_laranja": {
        "name": "Bolo de Laranja",
        "amount_cents": 4500,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_cenoura": {
        "name": "Bolo de Cenoura",
        "amount_cents": 4800,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "mini_bolo_iogurte": {
        "name": "Mini Bolo de Iogurte",
        "amount_cents": 2100,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_canetinha": {
        "name": "Bolo Canetinha",
        "amount_cents": 3700,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
    "bolo_nozes": {
        "name": "Bolo de Nozes",
        "amount_cents": 5500,
        "currency": "BRL",
        "imageURL": "",
        "is_active": True,
    },
}

SLOT_PLAN = {
    1: "bolo_laranja",
    2: "bolo_cenoura",
    3: "mini_bolo_iogurte",
    4: "bolo_canetinha",
    5: "bolo_nozes",
    6: "bolo_laranja",
    7: "bolo_cenoura",
    8: "mini_bolo_iogurte",
    9: "bolo_canetinha",
    10: "bolo_nozes",
    11: "bolo_laranja",
    12: "bolo_cenoura",
    13: "mini_bolo_iogurte",
    14: "bolo_canetinha",
    15: "bolo_nozes",
    16: "bolo_laranja",
    17: "bolo_cenoura",
    18: "mini_bolo_iogurte",
    19: "bolo_canetinha",
    20: "bolo_nozes",
    21: "bolo_laranja",
    22: "bolo_cenoura",
    23: "mini_bolo_iogurte",
    24: "bolo_canetinha",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sku_out(sku_id: str, item: dict) -> dict:
    return {
        "sku_id": sku_id,
        "name": item["name"],
        "amount_cents": int(item["amount_cents"]),
        "currency": item.get("currency", "BRL"),
        "imageURL": item.get("imageURL", ""),
        "is_active": bool(item.get("is_active", True)),
        "updated_at": _now_iso(),
    }


@router.get("/skus")
def list_skus():
    return [
        _sku_out(sku_id, item)
        for sku_id, item in SKU_CATALOG.items()
        if item.get("is_active", True)
    ]


@router.get("/skus/{sku_id}")
def get_sku(sku_id: str):
    item = SKU_CATALOG.get(sku_id)
    if not item or not item.get("is_active", True):
        raise HTTPException(status_code=404, detail="sku not found or inactive")

    return _sku_out(sku_id, item)


@router.get("/slots")
def list_catalog_slots():
    items = []

    for slot in range(1, 25):
        sku_id = SLOT_PLAN.get(slot)
        item = SKU_CATALOG.get(sku_id) if sku_id else None

        items.append(
            {
                "slot": slot,
                "sku_id": sku_id,
                "name": item["name"] if item else None,
                "amount_cents": int(item["amount_cents"]) if item else None,
                "currency": item.get("currency", "BRL") if item else "BRL",
                "imageURL": item.get("imageURL", "") if item else "",
                "is_active": bool(item.get("is_active", True)) if item else False,
                "updated_at": _now_iso(),
            }
        )

    return items