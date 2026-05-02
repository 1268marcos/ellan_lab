"""OPS: product_locker_configs por locker (listar / associar / remover)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db

router = APIRouter(
    prefix="/locker",
    tags=["locker-product-configs"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao"}))],
)

_LIST_SQL = """
SELECT id, locker_id, category, subcategory, allowed, temperature_zone,
       requires_signature, requires_id_check, max_weight_g, max_width_mm, max_height_mm, max_depth_mm,
       is_hazardous, is_fragile, priority
FROM product_locker_configs
WHERE locker_id = :locker_id
ORDER BY category
"""


class ProductLockerConfigCreateIn(BaseModel):
    locker_id: str = Field(..., min_length=1, max_length=64)
    category: str = Field(..., min_length=1, max_length=64)
    subcategory: str | None = Field(None, max_length=64)
    allowed: bool = True
    temperature_zone: str = Field("ANY", max_length=32)
    requires_signature: bool = False
    requires_id_check: bool = False
    max_weight_g: int | None = None
    max_width_mm: int | None = None
    max_height_mm: int | None = None
    max_depth_mm: int | None = None
    is_hazardous: bool = False
    is_fragile: bool = False
    priority: int = 100


@router.get("/product-configs")
def list_product_locker_configs(locker_id: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    rows = db.execute(text(_LIST_SQL), {"locker_id": locker_id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/product-configs", status_code=status.HTTP_201_CREATED)
def create_product_locker_config(body: ProductLockerConfigCreateIn, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id FROM lockers WHERE id = :id LIMIT 1"),
        {"id": body.locker_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": body.locker_id})
    cat = db.execute(
        text("SELECT id FROM product_categories WHERE id = :id LIMIT 1"),
        {"id": body.category},
    ).mappings().first()
    if not cat:
        raise HTTPException(status_code=404, detail={"type": "CATEGORY_NOT_FOUND", "message": body.category})
    sql = """
INSERT INTO product_locker_configs (
  locker_id, category, subcategory, allowed, temperature_zone,
  requires_signature, requires_id_check, max_weight_g, max_width_mm, max_height_mm, max_depth_mm,
  is_fragile, is_hazardous, priority
) VALUES (
  :locker_id, :category, :subcategory, :allowed, :temperature_zone,
  :requires_signature, :requires_id_check, :max_weight_g, :max_width_mm, :max_height_mm, :max_depth_mm,
  :is_fragile, :is_hazardous, :priority
) RETURNING id
"""
    params = {
        "locker_id": body.locker_id,
        "category": body.category,
        "subcategory": body.subcategory,
        "allowed": body.allowed,
        "temperature_zone": body.temperature_zone,
        "requires_signature": body.requires_signature,
        "requires_id_check": body.requires_id_check,
        "max_weight_g": body.max_weight_g,
        "max_width_mm": body.max_width_mm,
        "max_height_mm": body.max_height_mm,
        "max_depth_mm": body.max_depth_mm,
        "is_fragile": body.is_fragile,
        "is_hazardous": body.is_hazardous,
        "priority": body.priority,
    }
    try:
        new_id = db.execute(text(sql), params).scalar_one()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"type": "DUPLICATE_LOCKER_CATEGORY", "message": "Já existe config para este locker e categoria."},
        )
    return {"id": int(new_id)}


@router.delete("/product-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_locker_config(config_id: int, db: Session = Depends(get_db)):
    r = db.execute(text("DELETE FROM product_locker_configs WHERE id = :id RETURNING id"), {"id": config_id}).first()
    if not r:
        raise HTTPException(status_code=404, detail={"type": "NOT_FOUND", "message": str(config_id)})
    db.commit()
    return None
