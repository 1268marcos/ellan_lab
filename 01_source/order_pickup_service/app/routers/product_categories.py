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

_CATEGORY_SELECT = """
    SELECT
        id, name, description, parent_category,
        default_temperature_zone, default_security_level,
        is_hazardous, requires_age_verification,
        requires_id, requires_signature,
        max_weight_g, max_width_mm, max_height_mm, max_depth_mm,
        created_at, updated_at
    FROM product_categories
"""


def _to_iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _meta_from_row(row: dict[str, Any]) -> dict[str, Any]:
    dtz = str(row.get("default_temperature_zone") or "AMBIENT")
    dsl = str(row.get("default_security_level") or "STANDARD")
    haz = bool(row.get("is_hazardous"))
    return {
        "temperature_zone": dtz,
        "security_level": dsl,
        "is_hazardous": haz,
        "default_temperature_zone": dtz,
        "default_security_level": dsl,
    }


def _row_to_out(row: dict[str, Any]) -> ProductCategoryOut:
    return ProductCategoryOut(
        id=str(row.get("id") or ""),
        name=str(row.get("name") or ""),
        description=(str(row["description"]) if row.get("description") is not None else None),
        parent_category=(str(row["parent_category"]) if row.get("parent_category") else None),
        is_active=True if row.get("is_active") is None else bool(row.get("is_active")),
        metadata_json=_meta_from_row(row),
        requires_age_verification=bool(row.get("requires_age_verification")),
        requires_id=bool(row.get("requires_id")),
        requires_signature=bool(row.get("requires_signature")),
        max_weight_g=(int(row["max_weight_g"]) if row.get("max_weight_g") is not None else None),
        max_width_mm=(int(row["max_width_mm"]) if row.get("max_width_mm") is not None else None),
        max_height_mm=(int(row["max_height_mm"]) if row.get("max_height_mm") is not None else None),
        max_depth_mm=(int(row["max_depth_mm"]) if row.get("max_depth_mm") is not None else None),
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


def _meta_to_columns(meta: dict[str, Any] | None) -> tuple[str, str, bool]:
    base = meta or {}
    dtz = str(base.get("temperature_zone") or base.get("default_temperature_zone") or "AMBIENT").strip()[:32] or "AMBIENT"
    dsl = str(base.get("security_level") or base.get("default_security_level") or "STANDARD").strip()[:32] or "STANDARD"
    haz = bool(base.get("is_hazardous", False))
    return dtz, dsl, haz


def _resolve_category_fields(
    payload_meta: dict[str, Any] | None,
    *,
    requires_age_verification: bool | None = None,
    requires_id: bool | None = None,
    requires_signature: bool | None = None,
    max_weight_g: int | None = None,
    max_width_mm: int | None = None,
    max_height_mm: int | None = None,
    max_depth_mm: int | None = None,
) -> dict[str, Any]:
    dtz, dsl, haz = _meta_to_columns(payload_meta)
    return {
        "dtz": dtz,
        "dsl": dsl,
        "haz": haz,
        "requires_age_verification": bool(requires_age_verification),
        "requires_id": bool(requires_id),
        "requires_signature": bool(requires_signature),
        "max_weight_g": max_weight_g,
        "max_width_mm": max_width_mm,
        "max_height_mm": max_height_mm,
        "max_depth_mm": max_depth_mm,
    }


@router.get("", response_model=ProductCategoryListOut)
def list_product_categories_ops(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            f"""
            {_CATEGORY_SELECT}
            ORDER BY CASE WHEN parent_category IS NULL THEN 0 ELSE 1 END, parent_category, id
            """
        )
    ).mappings().all()
    items = [_row_to_out(dict(r)) for r in rows]
    return ProductCategoryListOut(ok=True, items=items)


@router.get("/{category_id}", response_model=ProductCategoryOut)
def get_product_category_ops(category_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(f"{_CATEGORY_SELECT} WHERE id = :id"),
        {"id": category_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "CATEGORY_NOT_FOUND", "message": "Categoria não encontrada."})
    return _row_to_out(dict(row))


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
    fields = _resolve_category_fields(
        payload.metadata_json,
        requires_age_verification=payload.requires_age_verification,
        requires_id=payload.requires_id,
        requires_signature=payload.requires_signature,
        max_weight_g=payload.max_weight_g,
        max_width_mm=payload.max_width_mm,
        max_height_mm=payload.max_height_mm,
        max_depth_mm=payload.max_depth_mm,
    )
    db.execute(
        text(
            """
            INSERT INTO product_categories (
                id, name, description, parent_category,
                default_temperature_zone, default_security_level,
                is_hazardous, requires_age_verification,
                requires_id, requires_signature,
                max_weight_g, max_width_mm, max_height_mm, max_depth_mm,
                created_at, updated_at
            ) VALUES (
                :id, :name, :description, :parent_category,
                :dtz, :dsl, :haz, :requires_age_verification,
                :requires_id, :requires_signature,
                :max_weight_g, :max_width_mm, :max_height_mm, :max_depth_mm,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": pid,
            "name": str(payload.name).strip(),
            "description": (payload.description.strip() if payload.description else None),
            "parent_category": (str(payload.parent_category).strip() if payload.parent_category else None),
            **fields,
        },
    )
    db.commit()
    row = db.execute(text(f"{_CATEGORY_SELECT} WHERE id = :id"), {"id": pid}).mappings().first()
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
        ndtz, ndsl, nhaz = _meta_to_columns(payload.metadata_json)
        dtz, dsl, haz = ndtz, ndsl, nhaz

    requires_age = row.get("requires_age_verification") if payload.requires_age_verification is None else payload.requires_age_verification
    requires_id = row.get("requires_id") if payload.requires_id is None else payload.requires_id
    requires_sig = row.get("requires_signature") if payload.requires_signature is None else payload.requires_signature
    max_weight = row.get("max_weight_g") if payload.max_weight_g is None else payload.max_weight_g
    max_width = row.get("max_width_mm") if payload.max_width_mm is None else payload.max_width_mm
    max_height = row.get("max_height_mm") if payload.max_height_mm is None else payload.max_height_mm
    max_depth = row.get("max_depth_mm") if payload.max_depth_mm is None else payload.max_depth_mm

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
                requires_age_verification = :requires_age_verification,
                requires_id = :requires_id,
                requires_signature = :requires_signature,
                max_weight_g = :max_weight_g,
                max_width_mm = :max_width_mm,
                max_height_mm = :max_height_mm,
                max_depth_mm = :max_depth_mm,
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
            "requires_age_verification": bool(requires_age),
            "requires_id": bool(requires_id),
            "requires_signature": bool(requires_sig),
            "max_weight_g": max_weight,
            "max_width_mm": max_width,
            "max_height_mm": max_height,
            "max_depth_mm": max_depth,
        },
    )
    db.commit()
    row2 = db.execute(text(f"{_CATEGORY_SELECT} WHERE id = :id"), {"id": category_id}).mappings().first()
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
