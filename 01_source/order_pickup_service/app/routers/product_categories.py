from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.schemas.product_categories import (
    ProductCategoryCreateIn,
    ProductCategoryDeleteOut,
    ProductCategoryListOut,
    ProductCategoryOut,
    ProductCategoryUpdateIn,
)

router = APIRouter(
    prefix="/product-categories",
    tags=["product-categories"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao"}))],
)


def _to_iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _row_to_out(row: dict[str, Any]) -> ProductCategoryOut:
    dtz = str(row.get("default_temperature_zone") or "AMBIENT")
    dsl = str(row.get("default_security_level") or "STANDARD")
    haz = bool(row.get("is_hazardous"))
    meta: dict[str, Any] = {
        "temperature_zone": dtz,
        "security_level": dsl,
        "is_hazardous": haz,
    }
    return ProductCategoryOut(
        id=str(row.get("id") or ""),
        name=str(row.get("name") or ""),
        description=(str(row["description"]) if row.get("description") is not None else None),
        parent_category=(str(row["parent_category"]) if row.get("parent_category") else None),
        is_active=True if row.get("is_active") is None else bool(row.get("is_active")),
        metadata_json=meta,
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


def _meta_to_columns(meta: dict[str, Any] | None) -> tuple[str, str, bool, dict[str, Any]]:
    base = meta or {}
    dtz = str(base.get("temperature_zone") or base.get("default_temperature_zone") or "AMBIENT").strip()[:32] or "AMBIENT"
    dsl = str(base.get("security_level") or base.get("default_security_level") or "STANDARD").strip()[:32] or "STANDARD"
    haz = bool(base.get("is_hazardous", False))
    reserved = {"temperature_zone", "security_level", "is_hazardous", "default_temperature_zone", "default_security_level"}
    extra = {k: v for k, v in base.items() if k not in reserved}
    return dtz, dsl, haz, extra


@router.get("", response_model=ProductCategoryListOut)
def list_product_categories_ops(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
                id, name, description, parent_category,
                default_temperature_zone, default_security_level,
                is_hazardous, created_at, updated_at
            FROM product_categories
            ORDER BY CASE WHEN parent_category IS NULL THEN 0 ELSE 1 END, parent_category, id
            """
        )
    ).mappings().all()
    items = [_row_to_out(dict(r)) for r in rows]
    return ProductCategoryListOut(ok=True, items=items)


@router.post("", response_model=ProductCategoryOut)
def create_product_category_ops(payload: ProductCategoryCreateIn, db: Session = Depends(get_db)):
    pid = str(payload.id).strip()
    exists = db.execute(text("SELECT 1 FROM product_categories WHERE id = :id LIMIT 1"), {"id": pid}).scalar()
    if exists:
        raise HTTPException(status_code=409, detail={"type": "CATEGORY_EXISTS", "message": f"Categoria {pid} já existe."})
    if payload.parent_category:
        p = str(payload.parent_category).strip()
        prow = db.execute(text("SELECT id FROM product_categories WHERE id = :id LIMIT 1"), {"id": p}).first()
        if not prow:
            raise HTTPException(status_code=422, detail={"type": "PARENT_NOT_FOUND", "message": "parent_category inválido."})
    dtz, dsl, haz, _extra = _meta_to_columns(payload.metadata_json)
    db.execute(
        text(
            """
            INSERT INTO product_categories (
                id, name, description, parent_category,
                default_temperature_zone, default_security_level,
                is_hazardous, requires_age_verification,
                created_at, updated_at
            ) VALUES (
                :id, :name, :description, :parent_category,
                :dtz, :dsl, :haz, FALSE,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": pid,
            "name": str(payload.name).strip(),
            "description": (payload.description.strip() if payload.description else None),
            "parent_category": (str(payload.parent_category).strip() if payload.parent_category else None),
            "dtz": dtz,
            "dsl": dsl,
            "haz": haz,
        },
    )
    db.commit()
    row = db.execute(
        text("SELECT * FROM product_categories WHERE id = :id"),
        {"id": pid},
    ).mappings().first()
    return _row_to_out(dict(row or {}))


@router.patch("/{category_id}", response_model=ProductCategoryOut)
def update_product_category_ops(category_id: str, payload: ProductCategoryUpdateIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM product_categories WHERE id = :id"), {"id": category_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "CATEGORY_NOT_FOUND", "message": "Categoria não encontrada."})
    if payload.parent_category is not None:
        p = str(payload.parent_category).strip() if payload.parent_category else None
        if p == category_id:
            raise HTTPException(status_code=422, detail={"type": "INVALID_PARENT", "message": "parent_category não pode ser o próprio id."})
        if p:
            prow = db.execute(text("SELECT id FROM product_categories WHERE id = :id LIMIT 1"), {"id": p}).first()
            if not prow:
                raise HTTPException(status_code=422, detail={"type": "PARENT_NOT_FOUND", "message": "parent_category inválido."})
            cur = p
            for _ in range(256):
                if cur == category_id:
                    raise HTTPException(status_code=422, detail={"type": "CATEGORY_CYCLE", "message": "Ciclo na hierarquia."})
                parent_row = db.execute(
                    text("SELECT parent_category FROM product_categories WHERE id = :id"),
                    {"id": cur},
                ).mappings().first()
                if not parent_row or not parent_row.get("parent_category"):
                    break
                cur = str(parent_row.get("parent_category"))

    name = payload.name if payload.name is not None else row.get("name")
    description = row.get("description") if payload.description is None else payload.description
    parent = row.get("parent_category") if payload.parent_category is None else (str(payload.parent_category).strip() if payload.parent_category else None)

    dtz = str(row.get("default_temperature_zone") or "AMBIENT")
    dsl = str(row.get("default_security_level") or "STANDARD")
    haz = bool(row.get("is_hazardous"))
    if payload.metadata_json is not None:
        ndtz, ndsl, nhaz, _e = _meta_to_columns(payload.metadata_json)
        dtz, dsl, haz = ndtz, ndsl, nhaz

    db.execute(
        text(
            """
            UPDATE product_categories SET
                name = :name,
                description = :description,
                parent_category = :parent_category,
                default_temperature_zone = :dtz,
                default_security_level = :dsl,
                is_hazardous = :haz,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {
            "id": category_id,
            "name": str(name).strip(),
            "description": description,
            "parent_category": parent,
            "dtz": dtz,
            "dsl": dsl,
            "haz": haz,
        },
    )
    db.commit()
    row2 = db.execute(text("SELECT * FROM product_categories WHERE id = :id"), {"id": category_id}).mappings().first()
    return _row_to_out(dict(row2 or {}))


@router.delete("/{category_id}", response_model=ProductCategoryDeleteOut)
def delete_product_category_ops(category_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM product_categories WHERE id = :id"), {"id": category_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "CATEGORY_NOT_FOUND", "message": "Categoria não encontrada."})
    ch = int(
        db.execute(
            text("SELECT COUNT(*) FROM product_categories WHERE parent_category = :id"),
            {"id": category_id},
        ).scalar()
        or 0
    )
    if ch > 0:
        raise HTTPException(status_code=409, detail={"type": "CATEGORY_HAS_CHILDREN", "message": "Remova subcategorias antes."})
    pr = int(
        db.execute(
            text("SELECT COUNT(*) FROM products WHERE category_id = :id"),
            {"id": category_id},
        ).scalar()
        or 0
    )
    if pr > 0:
        raise HTTPException(status_code=409, detail={"type": "CATEGORY_IN_USE_PRODUCTS", "message": "Categoria vinculada a produtos."})
    cf = int(
        db.execute(
            text("SELECT COUNT(*) FROM product_locker_configs WHERE category = :id"),
            {"id": category_id},
        ).scalar()
        or 0
    )
    if cf > 0:
        raise HTTPException(status_code=409, detail={"type": "CATEGORY_IN_USE_LOCKER", "message": "Categoria vinculada a configs de locker."})
    db.execute(text("DELETE FROM product_categories WHERE id = :id"), {"id": category_id})
    db.commit()
    return ProductCategoryDeleteOut(ok=True, id=category_id)
