from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter(prefix="/catalog", tags=["catalog"])

# MVP: tabela em memória (depois você troca por Postgres)
# PT (EUR) e SP (BRL) podem ter mapas diferentes por instância.
SKU_CATALOG = {
    "bolo_laranja_algarve": {"name": "Bolo de Laranja do Algarve", "amount_cents": 850, "currency": "EUR", "is_active": True},
    "bolo_cenoura_alentejo": {"name": "Bolo de Cenoura do Alentejo", "amount_cents": 990, "currency": "EUR", "is_active": True},
    "mini_bolo_milho": {"name": "Mini Bolo de Milho (Fubá)", "amount_cents": 495, "currency": "EUR", "is_active": True},
    "bolo_rei": {"name": "Bolo Rei", "amount_cents": 889, "currency": "EUR", "is_active": True},
    "bolo_rainha": {"name": "Bolo Rainha", "amount_cents": 1099, "currency": "EUR", "is_active": True},
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
        "currency": item.get("currency", "EUR"),
        "is_active": bool(item.get("is_active", True)),
        "updated_at": now.isoformat(),
    }
