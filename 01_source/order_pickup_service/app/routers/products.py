from __future__ import annotations

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
from app.schemas.products import (
    ProductAssetDeleteOut,
    ProductBarcodeCreateIn,
    ProductBarcodeListOut,
    ProductBarcodeOut,
    ProductBarcodeUpdateIn,
    ProductListItemOut,
    ProductListOut,
    ProductMediaCreateIn,
    ProductMediaListOut,
    ProductMediaOut,
    ProductMediaUpdateIn,
    ProductStatusHistoryItemOut,
    ProductStatusHistoryListOut,
    ProductStatusOut,
    ProductStatusTransitionIn,
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
            category_id=(str(row.get("category_id")) if row.get("category_id") is not None else None),
            status=str(row.get("status") or "DRAFT"),
            is_active=bool(row.get("is_active")),
            updated_at=_to_iso_utc(row.get("updated_at")),
        )
        for row in rows
    ]
    return ProductListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


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
