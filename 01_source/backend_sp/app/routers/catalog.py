from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter(prefix="/catalog", tags=["catalog"])

# MVP: tabela em memória (depois você troca por Postgres)
# PT (EUR) e SP (BRL) podem ter mapas diferentes por instância.
SKU_CATALOG = {
    "bolo_laranja": {"name": "Bolo de Laranja", "amount_cents": 4500, "currency": "BRL", "is_active": True},
    "bolo_cenoura": {"name": "Bolo de Cenoura", "amount_cents": 4800, "currency": "BRL", "is_active": True},
    "mini_bolo_iogurte": {"name": "Mini Bolo de Iogurte", "amount_cents": 2100, "currency": "BRL", "is_active": True},
    "bolo_canetinha": {"name": "Bolo Canetinha", "amount_cents": 3700, "currency": "BRL", "is_active": True},
    "bolo_nozes": {"name": "Bolo de Nozes", "amount_cents": 5500, "currency": "BRL", "is_active": True},
}

@router.get("/skus/{sku_id}")
def get_sku(sku_id: str):
    item = SKU_CATALOG.get(sku_id)
    if not item or not item.get("is_active", True):
        raise HTTPException(status_code=404, detail="sku not found or inactive")

    now = datetime.now(timezone.utc)
    return {
        "sku_id": sku_id,
        "name": item["name"],
        "amount_cents": int(item["amount_cents"]),
        "currency": item.get("currency", "BRL"),
        "is_active": bool(item.get("is_active", True)),
        "updated_at": now.isoformat(),
    }