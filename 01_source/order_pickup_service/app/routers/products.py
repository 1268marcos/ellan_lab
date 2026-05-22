from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, asc, desc, func, select, table, column, text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.product_catalog_assets import ProductBarcode, ProductMedia
from app.models.product_status_history import ProductStatusHistory
from app.models.user import User
from app.services.ops_audit_service import record_ops_action_audit
from app.schemas.products import (
    ProductAssetDeleteOut,
    ProductBarcodeCreateIn,
    ProductBarcodeListOut,
    ProductBarcodeOut,
    ProductBarcodeUpdateIn,
    ProductCreateIn,
    ProductDeleteOut,
    ProductDetailOut,
    ProductListItemOut,
    ProductListOut,
    ProductPricePatchIn,
    ProductPricePatchOut,
    ProductMediaCreateIn,
    ProductMediaListOut,
    ProductMediaOut,
    ProductMediaUpdateIn,
    ProductStatusHistoryItemOut,
    ProductStatusHistoryListOut,
    ProductStatusOut,
    ProductStatusTransitionIn,
    ProductUpdateIn,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

_PRODUCT_STATUSES = {"DRAFT", "ACTIVE", "INACTIVE", "DISCONTINUED"}
_ALLOWED_PRODUCT_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"ACTIVE", "DISCONTINUED"},
    "ACTIVE": {"INACTIVE", "DISCONTINUED"},
    "INACTIVE": {"ACTIVE", "DISCONTINUED"},
    "DISCONTINUED": set(),
}

products_table = table(
    "products",
    column("id"),
    column("name"),
    column("amount_cents"),
    column("category_id"),
    column("status"),
    column("is_active"),
    column("updated_at"),
)


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _load_product_status(db: Session, product_id: str) -> str:
    row = db.execute(
        text("SELECT id, COALESCE(status, 'DRAFT') AS status FROM products WHERE id = :id"),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PRODUCT_NOT_FOUND",
                "message": "Produto não encontrado.",
                "product_id": product_id,
            },
        )
    return str(row.get("status") or "DRAFT").strip().upper()


def _parse_iso_datetime_utc_optional(raw_value: str | None, *, field_name: str) -> datetime | None:
    value = str(raw_value or "").strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATETIME", "message": f"{field_name} inválido. Use ISO-8601."},
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ensure_product_exists(db: Session, product_id: str) -> None:
    _load_product_status(db, product_id=product_id)


def _ensure_category_exists(db: Session, category_id: str | None) -> None:
    if not category_id:
        return
    cid = str(category_id).strip()
    if not cid:
        return
    row = db.execute(text("SELECT id FROM product_categories WHERE id = :id LIMIT 1"), {"id": cid}).first()
    if not row:
        raise HTTPException(
            status_code=422,
            detail={"type": "CATEGORY_NOT_FOUND", "message": "category_id inválido.", "category_id": cid},
        )


def _normalize_product_status(raw: str | None) -> str:
    status = str(raw or "DRAFT").strip().upper()
    if status not in _PRODUCT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_PRODUCT_STATUS",
                "message": "Status inválido para produto.",
                "allowed_statuses": sorted(_PRODUCT_STATUSES),
            },
        )
    return status


def _parse_metadata_json(raw: object) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _row_to_detail(row: dict) -> ProductDetailOut:
    meta = _parse_metadata_json(row.get("metadata_json"))
    return ProductDetailOut(
        id=str(row.get("id") or ""),
        name=str(row.get("name") or ""),
        description=(str(row["description"]) if row.get("description") is not None else None),
        amount_cents=int(row.get("amount_cents") or 0),
        currency=str(row.get("currency") or "BRL"),
        category_id=(str(row["category_id"]) if row.get("category_id") is not None else None),
        width_mm=(int(row["width_mm"]) if row.get("width_mm") is not None else None),
        height_mm=(int(row["height_mm"]) if row.get("height_mm") is not None else None),
        depth_mm=(int(row["depth_mm"]) if row.get("depth_mm") is not None else None),
        weight_g=(int(row["weight_g"]) if row.get("weight_g") is not None else None),
        status=str(row.get("status") or "DRAFT"),
        is_active=bool(row.get("is_active")),
        requires_age_verification=bool(row.get("requires_age_verification")),
        requires_id_check=bool(row.get("requires_id_check")),
        requires_signature=bool(row.get("requires_signature")),
        is_hazardous=bool(row.get("is_hazardous")),
        is_fragile=bool(row.get("is_fragile")),
        is_virtual=bool(row.get("is_virtual")),
        metadata_json=meta,
        created_at=_to_iso_utc(row.get("created_at")),
        updated_at=_to_iso_utc(row.get("updated_at")),
    )


def _fetch_product_detail(db: Session, product_id: str) -> ProductDetailOut:
    row = db.execute(
        text(
            """
            SELECT
                id, name, description, amount_cents, currency, category_id,
                width_mm, height_mm, depth_mm, weight_g,
                COALESCE(status, 'DRAFT') AS status,
                COALESCE(is_active, FALSE) AS is_active,
                COALESCE(requires_age_verification, FALSE) AS requires_age_verification,
                COALESCE(requires_id_check, FALSE) AS requires_id_check,
                COALESCE(requires_signature, FALSE) AS requires_signature,
                COALESCE(is_hazardous, FALSE) AS is_hazardous,
                COALESCE(is_fragile, FALSE) AS is_fragile,
                COALESCE(is_virtual, FALSE) AS is_virtual,
                COALESCE(metadata_json, '{}') AS metadata_json,
                created_at, updated_at
            FROM products
            WHERE id = :id
            """
        ),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PRODUCT_NOT_FOUND",
                "message": "Produto não encontrado.",
                "product_id": product_id,
            },
        )
    return _row_to_detail(dict(row))


def _record_product_price_audit(
    *,
    db: Session,
    correlation_id: str,
    actor_user_id: str | None,
    action: str,
    old_value: int,
    new_value: int,
    product_id: str,
) -> None:
    try:
        record_ops_action_audit(
            db=db,
            action=action,
            result="OK",
            correlation_id=correlation_id,
            user_id=actor_user_id,
            role=None,
            order_id=None,
            details={
                "actor": actor_user_id,
                "old_value": old_value,
                "new_value": new_value,
                "product_id": product_id,
            },
        )
    except Exception:
        pass


def _to_media_out(row: ProductMedia) -> ProductMediaOut:
    return ProductMediaOut(
        id=row.id,
        product_id=row.product_id,
        media_type=row.media_type,
        url=row.url,
        cdn_key=row.cdn_key,
        alt_text=row.alt_text,
        sort_order=int(row.sort_order or 0),
        is_primary=bool(row.is_primary),
        created_at=_to_iso_utc(row.created_at),
    )


def _to_barcode_out(row: ProductBarcode) -> ProductBarcodeOut:
    return ProductBarcodeOut(
        id=row.id,
        product_id=row.product_id,
        barcode_type=row.barcode_type,
        barcode_value=row.barcode_value,
        is_primary=bool(row.is_primary),
        created_at=_to_iso_utc(row.created_at),
    )


@router.get("", response_model=ProductListOut)
def list_products(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    updated_from: str | None = Query(default=None),
    updated_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    normalized_status = str(status or "").strip().upper()
    if normalized_status and normalized_status not in _PRODUCT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_PRODUCT_STATUS",
                "message": "Status inválido para filtro de produtos.",
                "allowed_statuses": sorted(_PRODUCT_STATUSES),
            },
        )
    normalized_category = str(category or "").strip()
    dt_from = _parse_iso_datetime_utc_optional(updated_from, field_name="updated_from")
    dt_to = _parse_iso_datetime_utc_optional(updated_to, field_name="updated_to")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "updated_from deve ser <= updated_to."},
        )

    filters = []
    if normalized_status:
        filters.append(func.coalesce(products_table.c.status, "DRAFT") == normalized_status)
    if normalized_category:
        filters.append(products_table.c.category_id == normalized_category)
    if dt_from is not None:
        filters.append(products_table.c.updated_at >= dt_from)
    if dt_to is not None:
        filters.append(products_table.c.updated_at <= dt_to)

    where_expr = and_(*filters) if filters else None
    total_stmt = select(func.count()).select_from(products_table)
    if where_expr is not None:
        total_stmt = total_stmt.where(where_expr)
    total = int(db.execute(total_stmt).scalar() or 0)

    rows_stmt = (
        select(
            products_table.c.id,
            products_table.c.name,
            products_table.c.amount_cents,
            products_table.c.category_id,
            func.coalesce(products_table.c.status, "DRAFT").label("status"),
            func.coalesce(products_table.c.is_active, False).label("is_active"),
            products_table.c.updated_at,
        )
        .select_from(products_table)
        .order_by(desc(products_table.c.updated_at), desc(products_table.c.id))
        .limit(int(limit))
        .offset(int(offset))
    )
    if where_expr is not None:
        rows_stmt = rows_stmt.where(where_expr)

    rows = db.execute(rows_stmt).mappings().all()

    items = [
        ProductListItemOut(
            id=str(row.get("id") or ""),
            name=str(row.get("name") or ""),
            amount_cents=int(row.get("amount_cents") or 0),
            category_id=(str(row.get("category_id")) if row.get("category_id") is not None else None),
            status=str(row.get("status") or "DRAFT"),
            is_active=bool(row.get("is_active")),
            updated_at=_to_iso_utc(row.get("updated_at")),
        )
        for row in rows
    ]
    return ProductListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("", response_model=ProductDetailOut, status_code=201)
def create_product_ops(payload: ProductCreateIn, db: Session = Depends(get_db)):
    product_id = str(payload.id).strip()
    exists = db.execute(text("SELECT 1 FROM products WHERE id = :id LIMIT 1"), {"id": product_id}).scalar()
    if exists:
        raise HTTPException(
            status_code=409,
            detail={"type": "PRODUCT_EXISTS", "message": f"Produto {product_id} já existe.", "product_id": product_id},
        )
    _ensure_category_exists(db, payload.category_id)
    status = _normalize_product_status(payload.status)
    meta = payload.metadata_json if isinstance(payload.metadata_json, dict) else {}
    meta_json = json.dumps(meta)
    db.execute(
        text(
            """
            INSERT INTO products (
                id, name, description, amount_cents, currency, category_id,
                width_mm, height_mm, depth_mm, weight_g,
                is_active, requires_age_verification, requires_id_check, requires_signature,
                is_hazardous, is_fragile, is_virtual, metadata_json, status,
                created_at, updated_at
            ) VALUES (
                :id, :name, :description, :amount_cents, :currency, :category_id,
                :width_mm, :height_mm, :depth_mm, :weight_g,
                :is_active, :requires_age_verification, :requires_id_check, :requires_signature,
                :is_hazardous, :is_fragile, :is_virtual, :metadata_json, :status,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": product_id,
            "name": str(payload.name).strip(),
            "description": (payload.description.strip() if payload.description else None),
            "amount_cents": int(payload.amount_cents),
            "currency": str(payload.currency or "BRL").strip()[:8] or "BRL",
            "category_id": (str(payload.category_id).strip() if payload.category_id else None),
            "width_mm": payload.width_mm,
            "height_mm": payload.height_mm,
            "depth_mm": payload.depth_mm,
            "weight_g": payload.weight_g,
            "is_active": bool(payload.is_active),
            "requires_age_verification": bool(payload.requires_age_verification),
            "requires_id_check": bool(payload.requires_id_check),
            "requires_signature": bool(payload.requires_signature),
            "is_hazardous": bool(payload.is_hazardous),
            "is_fragile": bool(payload.is_fragile),
            "is_virtual": bool(payload.is_virtual),
            "metadata_json": meta_json,
            "status": status,
        },
    )
    db.commit()
    return _fetch_product_detail(db, product_id)


@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product_ops(product_id: str, db: Session = Depends(get_db)):
    return _fetch_product_detail(db, product_id)


@router.patch("/{product_id}", response_model=ProductDetailOut)
def update_product_ops(product_id: str, payload: ProductUpdateIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id}).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado.", "product_id": product_id},
        )
    if payload.category_id is not None:
        _ensure_category_exists(db, payload.category_id)

    name = str(payload.name).strip() if payload.name is not None else row.get("name")
    description = row.get("description") if payload.description is None else payload.description
    amount_cents = int(payload.amount_cents) if payload.amount_cents is not None else int(row.get("amount_cents") or 0)
    currency = str(payload.currency or row.get("currency") or "BRL").strip()[:8] or "BRL"
    category_id = row.get("category_id") if payload.category_id is None else (str(payload.category_id).strip() if payload.category_id else None)
    width_mm = row.get("width_mm") if payload.width_mm is None else payload.width_mm
    height_mm = row.get("height_mm") if payload.height_mm is None else payload.height_mm
    depth_mm = row.get("depth_mm") if payload.depth_mm is None else payload.depth_mm
    weight_g = row.get("weight_g") if payload.weight_g is None else payload.weight_g
    is_active = row.get("is_active") if payload.is_active is None else payload.is_active
    requires_age = row.get("requires_age_verification") if payload.requires_age_verification is None else payload.requires_age_verification
    requires_id = row.get("requires_id_check") if payload.requires_id_check is None else payload.requires_id_check
    requires_sig = row.get("requires_signature") if payload.requires_signature is None else payload.requires_signature
    is_hazardous = row.get("is_hazardous") if payload.is_hazardous is None else payload.is_hazardous
    is_fragile = row.get("is_fragile") if payload.is_fragile is None else payload.is_fragile
    is_virtual = row.get("is_virtual") if payload.is_virtual is None else payload.is_virtual
    meta = (
        _parse_metadata_json(row.get("metadata_json"))
        if payload.metadata_json is None
        else (payload.metadata_json if isinstance(payload.metadata_json, dict) else {})
    )
    meta_json = json.dumps(meta)

    db.execute(
        text(
            """
            UPDATE products SET
                name = :name,
                description = :description,
                amount_cents = :amount_cents,
                currency = :currency,
                category_id = :category_id,
                width_mm = :width_mm,
                height_mm = :height_mm,
                depth_mm = :depth_mm,
                weight_g = :weight_g,
                is_active = :is_active,
                requires_age_verification = :requires_age_verification,
                requires_id_check = :requires_id_check,
                requires_signature = :requires_signature,
                is_hazardous = :is_hazardous,
                is_fragile = :is_fragile,
                is_virtual = :is_virtual,
                metadata_json = :metadata_json,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {
            "id": product_id,
            "name": str(name).strip(),
            "description": description,
            "amount_cents": amount_cents,
            "currency": currency,
            "category_id": category_id,
            "width_mm": width_mm,
            "height_mm": height_mm,
            "depth_mm": depth_mm,
            "weight_g": weight_g,
            "is_active": bool(is_active),
            "requires_age_verification": bool(requires_age),
            "requires_id_check": bool(requires_id),
            "requires_signature": bool(requires_sig),
            "is_hazardous": bool(is_hazardous),
            "is_fragile": bool(is_fragile),
            "is_virtual": bool(is_virtual),
            "metadata_json": meta_json,
        },
    )
    db.commit()
    return _fetch_product_detail(db, product_id)


@router.delete("/{product_id}", response_model=ProductDeleteOut)
def deactivate_product_ops(product_id: str, db: Session = Depends(get_db)):
    _load_product_status(db, product_id=product_id)
    db.execute(
        text(
            """
            UPDATE products
            SET status = 'INACTIVE',
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {"id": product_id},
    )
    db.commit()
    return ProductDeleteOut(ok=True, product_id=product_id, status="INACTIVE")


@router.patch("/{product_id}/price", response_model=ProductPricePatchOut)
def patch_product_price(
    product_id: str,
    payload: ProductPricePatchIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT id, amount_cents, COALESCE(status, 'DRAFT') AS status
            FROM products
            WHERE id = :id
            """
        ),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PRODUCT_NOT_FOUND",
                "message": "Produto não encontrado.",
                "product_id": product_id,
            },
        )
    status = str(row.get("status") or "DRAFT").strip().upper()
    if status not in {"DRAFT", "ACTIVE"}:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "PRODUCT_PRICE_STATUS_NOT_ALLOWED",
                "message": "Preço só pode ser editado para produtos em DRAFT ou ACTIVE.",
                "status": status,
            },
        )
    old_cents = int(row.get("amount_cents") or 0)
    new_cents = int(payload.amount_cents)

    db.execute(
        text(
            """
            UPDATE products
            SET amount_cents = :amount_cents,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {"id": product_id, "amount_cents": new_cents},
    )
    actor_id = str(current_user.id) if current_user and current_user.id else None
    _record_product_price_audit(
        db=db,
        correlation_id=str(uuid4()),
        actor_user_id=actor_id,
        action="PRODUCT_PRICE_UPDATE",
        old_value=old_cents,
        new_value=new_cents,
        product_id=product_id,
    )
    db.commit()

    return ProductPricePatchOut(ok=True, product_id=product_id, amount_cents=new_cents)


@router.patch("/{product_id}/status", response_model=ProductStatusOut)
def patch_product_status(
    product_id: str,
    payload: ProductStatusTransitionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    to_status = str(payload.to_status or "").strip().upper()
    if to_status not in _PRODUCT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_PRODUCT_STATUS",
                "message": "Status inválido para produto.",
                "allowed_statuses": sorted(_PRODUCT_STATUSES),
            },
        )

    from_status = _load_product_status(db, product_id=product_id)
    if from_status == to_status:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "STATUS_UNCHANGED",
                "message": "O produto já está nesse status.",
                "status": to_status,
            },
        )

    allowed_targets = _ALLOWED_PRODUCT_TRANSITIONS.get(from_status, set())
    if to_status not in allowed_targets:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_STATUS_TRANSITION",
                "message": "Transição de status não permitida para produto.",
                "from_status": from_status,
                "to_status": to_status,
                "allowed_targets": sorted(allowed_targets),
            },
        )

    db.execute(
        text(
            """
            UPDATE products
            SET status = :status,
                updated_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": product_id, "status": to_status},
    )

    changed_at = datetime.now(timezone.utc)
    history_row = ProductStatusHistory(
        id=str(uuid4()),
        product_id=product_id,
        from_status=from_status,
        to_status=to_status,
        reason=(payload.reason.strip() if payload.reason else None),
        changed_by=str(current_user.id) if current_user and current_user.id else None,
        changed_at=changed_at,
    )
    db.add(history_row)
    db.commit()

    return ProductStatusOut(
        ok=True,
        product_id=product_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=history_row.changed_by,
        changed_at=_to_iso_utc(changed_at),
    )


@router.get("/{product_id}/status-history", response_model=ProductStatusHistoryListOut)
def get_product_status_history(
    product_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_product_status(db, product_id=product_id)

    rows = (
        db.query(ProductStatusHistory)
        .filter(ProductStatusHistory.product_id == product_id)
        .order_by(ProductStatusHistory.changed_at.desc(), ProductStatusHistory.id.desc())
        .limit(limit)
        .all()
    )

    items = [
        ProductStatusHistoryItemOut(
            id=row.id,
            product_id=row.product_id,
            from_status=row.from_status,
            to_status=row.to_status,
            reason=row.reason,
            changed_by=row.changed_by,
            changed_at=_to_iso_utc(row.changed_at),
        )
        for row in rows
    ]
    return ProductStatusHistoryListOut(ok=True, total=len(items), items=items)


@router.post("/{product_id}/media", response_model=ProductMediaOut)
def post_product_media(
    product_id: str,
    payload: ProductMediaCreateIn,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    media_type = str(payload.media_type or "").strip().upper()
    if media_type not in {"IMAGE", "VIDEO", "PDF", "3D"}:
        raise HTTPException(status_code=422, detail={"type": "INVALID_MEDIA_TYPE", "allowed_media_types": ["3D", "IMAGE", "PDF", "VIDEO"]})
    if payload.is_primary:
        db.query(ProductMedia).filter(ProductMedia.product_id == product_id, ProductMedia.is_primary.is_(True)).update({"is_primary": False})
    row = ProductMedia(
        id=str(uuid4()),
        product_id=product_id,
        media_type=media_type,
        url=str(payload.url).strip(),
        cdn_key=(payload.cdn_key.strip() if payload.cdn_key else None),
        alt_text=(payload.alt_text.strip() if payload.alt_text else None),
        sort_order=int(payload.sort_order),
        is_primary=bool(payload.is_primary),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    return _to_media_out(row)


@router.get("/{product_id}/media", response_model=ProductMediaListOut)
def list_product_media(
    product_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    rows = (
        db.query(ProductMedia)
        .filter(ProductMedia.product_id == product_id)
        .order_by(ProductMedia.is_primary.desc(), ProductMedia.sort_order.asc(), ProductMedia.created_at.desc())
        .limit(limit)
        .all()
    )
    return ProductMediaListOut(ok=True, total=len(rows), items=[_to_media_out(row) for row in rows])


@router.patch("/{product_id}/media/{media_id}", response_model=ProductMediaOut)
def patch_product_media(
    product_id: str,
    media_id: str,
    payload: ProductMediaUpdateIn,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    row = (
        db.query(ProductMedia)
        .filter(ProductMedia.id == media_id, ProductMedia.product_id == product_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_MEDIA_NOT_FOUND", "message": "Mídia não encontrada para o produto."},
        )
    if payload.media_type is not None:
        media_type = str(payload.media_type or "").strip().upper()
        if media_type not in {"IMAGE", "VIDEO", "PDF", "3D"}:
            raise HTTPException(status_code=422, detail={"type": "INVALID_MEDIA_TYPE", "allowed_media_types": ["3D", "IMAGE", "PDF", "VIDEO"]})
        row.media_type = media_type
    if payload.url is not None:
        row.url = str(payload.url).strip()
    if payload.cdn_key is not None:
        row.cdn_key = payload.cdn_key.strip() if payload.cdn_key else None
    if payload.alt_text is not None:
        row.alt_text = payload.alt_text.strip() if payload.alt_text else None
    if payload.sort_order is not None:
        row.sort_order = int(payload.sort_order)
    if payload.is_primary is not None:
        next_is_primary = bool(payload.is_primary)
        if next_is_primary:
            db.query(ProductMedia).filter(
                ProductMedia.product_id == product_id,
                ProductMedia.id != media_id,
                ProductMedia.is_primary.is_(True),
            ).update({"is_primary": False})
        row.is_primary = next_is_primary
    db.commit()
    return _to_media_out(row)


@router.post("/{product_id}/barcodes", response_model=ProductBarcodeOut)
def post_product_barcode(
    product_id: str,
    payload: ProductBarcodeCreateIn,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    barcode_type = str(payload.barcode_type or "").strip().upper()
    if barcode_type not in {"EAN13", "EAN8", "GTIN14", "QR", "CODE128", "DATAMATRIX"}:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_BARCODE_TYPE", "allowed_barcode_types": ["CODE128", "DATAMATRIX", "EAN13", "EAN8", "GTIN14", "QR"]},
        )
    barcode_value = str(payload.barcode_value or "").strip().upper()
    existing = db.query(ProductBarcode).filter(ProductBarcode.barcode_value == barcode_value).first()
    if existing and existing.product_id != product_id:
        raise HTTPException(status_code=409, detail={"type": "BARCODE_ALREADY_ASSIGNED", "message": "barcode_value já vinculado a outro produto."})
    if existing and existing.product_id == product_id:
        return _to_barcode_out(existing)
    if payload.is_primary:
        db.query(ProductBarcode).filter(ProductBarcode.product_id == product_id, ProductBarcode.is_primary.is_(True)).update({"is_primary": False})
    row = ProductBarcode(
        id=str(uuid4()),
        product_id=product_id,
        barcode_type=barcode_type,
        barcode_value=barcode_value,
        is_primary=bool(payload.is_primary),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    return _to_barcode_out(row)


@router.get("/{product_id}/barcodes", response_model=ProductBarcodeListOut)
def list_product_barcodes(
    product_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    rows = (
        db.query(ProductBarcode)
        .filter(ProductBarcode.product_id == product_id)
        .order_by(ProductBarcode.is_primary.desc(), ProductBarcode.created_at.desc())
        .limit(limit)
        .all()
    )
    return ProductBarcodeListOut(ok=True, total=len(rows), items=[_to_barcode_out(row) for row in rows])


@router.patch("/{product_id}/barcodes/{barcode_id}", response_model=ProductBarcodeOut)
def patch_product_barcode(
    product_id: str,
    barcode_id: str,
    payload: ProductBarcodeUpdateIn,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    row = (
        db.query(ProductBarcode)
        .filter(ProductBarcode.id == barcode_id, ProductBarcode.product_id == product_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_BARCODE_NOT_FOUND", "message": "Barcode não encontrado para o produto."},
        )
    if payload.barcode_type is not None:
        barcode_type = str(payload.barcode_type or "").strip().upper()
        if barcode_type not in {"EAN13", "EAN8", "GTIN14", "QR", "CODE128", "DATAMATRIX"}:
            raise HTTPException(
                status_code=422,
                detail={"type": "INVALID_BARCODE_TYPE", "allowed_barcode_types": ["CODE128", "DATAMATRIX", "EAN13", "EAN8", "GTIN14", "QR"]},
            )
        row.barcode_type = barcode_type
    if payload.barcode_value is not None:
        barcode_value = str(payload.barcode_value or "").strip().upper()
        conflict = (
            db.query(ProductBarcode)
            .filter(
                ProductBarcode.barcode_value == barcode_value,
                ProductBarcode.id != barcode_id,
            )
            .first()
        )
        if conflict:
            raise HTTPException(status_code=409, detail={"type": "BARCODE_ALREADY_ASSIGNED", "message": "barcode_value já vinculado a outro produto."})
        row.barcode_value = barcode_value
    if payload.is_primary is not None:
        next_is_primary = bool(payload.is_primary)
        if next_is_primary:
            db.query(ProductBarcode).filter(
                ProductBarcode.product_id == product_id,
                ProductBarcode.id != barcode_id,
                ProductBarcode.is_primary.is_(True),
            ).update({"is_primary": False})
        row.is_primary = next_is_primary
    db.commit()
    return _to_barcode_out(row)


@router.delete("/{product_id}/media/{media_id}", response_model=ProductAssetDeleteOut)
def delete_product_media(
    product_id: str,
    media_id: str,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    row = (
        db.query(ProductMedia)
        .filter(ProductMedia.id == media_id, ProductMedia.product_id == product_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_MEDIA_NOT_FOUND", "message": "Mídia não encontrada para o produto."},
        )
    db.delete(row)
    db.commit()
    return ProductAssetDeleteOut(ok=True, product_id=product_id, deleted_id=media_id, deleted_type="MEDIA")


@router.delete("/{product_id}/barcodes/{barcode_id}", response_model=ProductAssetDeleteOut)
def delete_product_barcode(
    product_id: str,
    barcode_id: str,
    db: Session = Depends(get_db),
):
    _ensure_product_exists(db, product_id)
    row = (
        db.query(ProductBarcode)
        .filter(ProductBarcode.id == barcode_id, ProductBarcode.product_id == product_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_BARCODE_NOT_FOUND", "message": "Barcode não encontrado para o produto."},
        )
    db.delete(row)
    db.commit()
    return ProductAssetDeleteOut(ok=True, product_id=product_id, deleted_id=barcode_id, deleted_type="BARCODE")
