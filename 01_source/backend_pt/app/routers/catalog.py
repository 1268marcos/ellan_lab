from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

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

SLOT_PLAN = {
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sku_out(sku_id: str, item: dict) -> dict:
    return {
        "sku_id": sku_id,
        "name": item["name"],
        "amount_cents": int(item["amount_cents"]),
        "currency": item.get("currency", "EUR"),
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
                "currency": item.get("currency", "EUR") if item else "EUR",
                "imageURL": item.get("imageURL", "") if item else "",
                "is_active": bool(item.get("is_active", True)) if item else False,
                "updated_at": _now_iso(),
            }
        )

    return items