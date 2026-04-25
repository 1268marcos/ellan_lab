from __future__ import annotations

import json
from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.user import User
from app.schemas.pricing_fiscal import (
    FiscalAutoClassificationLogItemOut,
    FiscalAutoClassificationLogListOut,
    ProductBundleItemOut,
    ProductBundleCreateIn,
    ProductBundleListOut,
    ProductBundleOut,
    ProductBundleItemCreateIn,
    ProductFiscalConfigOut,
    ProductFiscalConfigUpsertIn,
    ProductFiscalConfigUpsertOut,
    PromotionCreateIn,
    PromotionListOut,
    PromotionOut,
    PromotionStatusPatchIn,
    PromotionStatusOut,
    PromotionValidateIn,
    PromotionValidateOut,
)
from app.services.ops_audit_service import record_ops_action_audit

router = APIRouter(
    tags=["pricing-fiscal"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)


def _resolve_correlation_id(header_value: str | None) -> str:
    raw = str(header_value or "").strip()
    return raw or f"corr-pr3-{uuid4().hex}"


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso_datetime_utc_optional(raw_value: str | None, *, field_name: str) -> datetime | None:
    raw = str(raw_value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
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


def _json_load_dict(value, default: dict | None = None) -> dict:
    fallback = default or {}
    if value is None:
        return fallback
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        import json

        try:
            decoded = json.loads(value)
            if isinstance(decoded, dict):
                return decoded
        except Exception:
            return fallback
    return fallback


def _to_audit_payload(value):
    if isinstance(value, datetime):
        return _to_iso_utc(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _to_audit_payload(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_audit_payload(v) for v in value]
    return value


def _promotion_to_out(row: dict) -> PromotionOut:
    return PromotionOut(
        id=str(row.get("id") or ""),
        code=(str(row.get("code")) if row.get("code") is not None else None),
        name=str(row.get("name") or ""),
        type=str(row.get("type") or ""),
        discount_pct=(float(row.get("discount_pct")) if row.get("discount_pct") is not None else None),
        discount_cents=(int(row.get("discount_cents")) if row.get("discount_cents") is not None else None),
        min_order_cents=int(row.get("min_order_cents") or 0),
        max_discount_cents=(int(row.get("max_discount_cents")) if row.get("max_discount_cents") is not None else None),
        max_uses=(int(row.get("max_uses")) if row.get("max_uses") is not None else None),
        uses_count=int(row.get("uses_count") or 0),
        per_user_limit=(int(row.get("per_user_limit")) if row.get("per_user_limit") is not None else None),
        conditions_json=_json_load_dict(row.get("conditions_json"), default={}),
        is_active=bool(row.get("is_active")),
        valid_from=_to_iso_utc(row.get("valid_from")),
        valid_until=(_to_iso_utc(row.get("valid_until")) if row.get("valid_until") else None),
        created_by=(str(row.get("created_by")) if row.get("created_by") is not None else None),
        created_at=_to_iso_utc(row.get("created_at")),
    )


def _record_pr3_audit(
    *,
    db: Session,
    correlation_id: str,
    current_user: User,
    action: str,
    result: str = "SUCCESS",
    error_message: str | None = None,
    order_id: str | None = None,
    payload: dict,
) -> None:
    record_ops_action_audit(
        db=db,
        action=action,
        result=result,
        correlation_id=correlation_id,
        user_id=str(current_user.id) if current_user and current_user.id else None,
        role="admin_operacao",
        order_id=order_id,
        error_message=error_message,
        details={
            **_to_audit_payload(payload),
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/products/bundles", response_model=ProductBundleListOut)
def list_product_bundles(
    is_active: bool | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    dt_from = _parse_iso_datetime_utc_optional(from_date, field_name="from_date")
    dt_to = _parse_iso_datetime_utc_optional(to_date, field_name="to_date")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from_date deve ser <= to_date."},
        )
    where_parts = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    if is_active is not None:
        where_parts.append("is_active = :is_active")
        params["is_active"] = bool(is_active)
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)
    total_row = db.execute(
        text(f"SELECT COUNT(*) AS total FROM product_bundles WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT id, name, code, description, amount_cents, currency, bundle_type, is_active,
                   valid_from, valid_until, created_at, updated_at
            FROM product_bundles
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [
        ProductBundleOut(
            id=str(row.get("id") or ""),
            name=str(row.get("name") or ""),
            code=str(row.get("code") or ""),
            description=(str(row.get("description")) if row.get("description") is not None else None),
            amount_cents=int(row.get("amount_cents") or 0),
            currency=str(row.get("currency") or "BRL"),
            bundle_type=str(row.get("bundle_type") or "FIXED"),
            is_active=bool(row.get("is_active")),
            valid_from=(_to_iso_utc(row.get("valid_from")) if row.get("valid_from") else None),
            valid_until=(_to_iso_utc(row.get("valid_until")) if row.get("valid_until") else None),
            created_at=_to_iso_utc(row.get("created_at")),
            updated_at=_to_iso_utc(row.get("updated_at")),
        )
        for row in rows
    ]
    return ProductBundleListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/products/bundles", response_model=ProductBundleOut)
def create_product_bundle(
    payload: ProductBundleCreateIn,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row_id = str(uuid4())
    data = payload.model_dump(mode="json")
    try:
        db.execute(
            text(
                """
                INSERT INTO product_bundles (
                    id, name, code, description, amount_cents, currency, bundle_type, is_active,
                    valid_from, valid_until, created_at, updated_at
                ) VALUES (
                    :id, :name, :code, :description, :amount_cents, :currency, :bundle_type, TRUE,
                    :valid_from, :valid_until, NOW(), NOW()
                )
                """
            ),
            {
                "id": row_id,
                **data,
            },
        )
        _record_pr3_audit(
            db=db,
            correlation_id=corr_id,
            current_user=current_user,
            action="PR3_BUNDLE_CREATE",
            payload={"after": {"id": row_id, **data}},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _record_pr3_audit(
            db=db,
            correlation_id=corr_id,
            current_user=current_user,
            action="PR3_BUNDLE_CREATE",
            result="ERROR",
            error_message=str(exc),
            payload={"attempted_after": {"id": row_id, **data}},
        )
        db.commit()
        raise HTTPException(
            status_code=422,
            detail={"type": "BUNDLE_CREATE_FAILED", "message": "Não foi possível criar bundle.", "error": str(exc)},
        ) from exc

    created = db.execute(
        text(
            """
            SELECT id, name, code, description, amount_cents, currency, bundle_type, is_active,
                   valid_from, valid_until, created_at, updated_at
            FROM product_bundles
            WHERE id = :id
            """
        ),
        {"id": row_id},
    ).mappings().first()
    return ProductBundleOut(
        id=str(created.get("id") or ""),
        name=str(created.get("name") or ""),
        code=str(created.get("code") or ""),
        description=(str(created.get("description")) if created.get("description") is not None else None),
        amount_cents=int(created.get("amount_cents") or 0),
        currency=str(created.get("currency") or "BRL"),
        bundle_type=str(created.get("bundle_type") or "FIXED"),
        is_active=bool(created.get("is_active")),
        valid_from=(_to_iso_utc(created.get("valid_from")) if created.get("valid_from") else None),
        valid_until=(_to_iso_utc(created.get("valid_until")) if created.get("valid_until") else None),
        created_at=_to_iso_utc(created.get("created_at")),
        updated_at=_to_iso_utc(created.get("updated_at")),
    )


@router.post("/products/bundles/{bundle_id}/items", response_model=ProductBundleItemOut)
def add_product_bundle_item(
    bundle_id: str,
    payload: ProductBundleItemCreateIn,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bundle_exists = db.execute(
        text("SELECT id FROM product_bundles WHERE id = :id"),
        {"id": bundle_id},
    ).mappings().first()
    if not bundle_exists:
        raise HTTPException(
            status_code=404,
            detail={"type": "BUNDLE_NOT_FOUND", "message": "Bundle não encontrado.", "bundle_id": bundle_id},
        )
    product_exists = db.execute(
        text("SELECT id FROM products WHERE id = :id"),
        {"id": payload.product_id},
    ).mappings().first()
    if not product_exists:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado.", "product_id": payload.product_id},
        )
    corr_id = _resolve_correlation_id(correlation_id)
    row = db.execute(
        text(
            """
            INSERT INTO product_bundle_items (bundle_id, product_id, quantity, unit_price_cents, sort_order)
            VALUES (:bundle_id, :product_id, :quantity, :unit_price_cents, :sort_order)
            RETURNING id, bundle_id, product_id, quantity, unit_price_cents, sort_order
            """
        ),
        {"bundle_id": bundle_id, **payload.model_dump(mode="json")},
    ).mappings().first()
    _record_pr3_audit(
        db=db,
        correlation_id=corr_id,
        current_user=current_user,
        action="PR3_BUNDLE_ITEM_ADD",
        payload={"before": None, "after": dict(row or {})},
    )
    db.commit()
    return ProductBundleItemOut(
        id=int(row.get("id")),
        bundle_id=str(row.get("bundle_id") or ""),
        product_id=str(row.get("product_id") or ""),
        quantity=int(row.get("quantity") or 1),
        unit_price_cents=(int(row.get("unit_price_cents")) if row.get("unit_price_cents") is not None else None),
        sort_order=int(row.get("sort_order") or 0),
    )


@router.get("/promotions", response_model=PromotionListOut)
def list_promotions(
    is_active: bool | None = Query(default=None),
    code: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    dt_from = _parse_iso_datetime_utc_optional(from_date, field_name="from_date")
    dt_to = _parse_iso_datetime_utc_optional(to_date, field_name="to_date")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from_date deve ser <= to_date."},
        )
    where_parts = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    normalized_code = str(code or "").strip()
    if is_active is not None:
        where_parts.append("is_active = :is_active")
        params["is_active"] = bool(is_active)
    if normalized_code:
        where_parts.append("code = :code")
        params["code"] = normalized_code
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)
    total_row = db.execute(
        text(f"SELECT COUNT(*) AS total FROM promotions WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT id, code, name, type, discount_pct, discount_cents, min_order_cents, max_discount_cents,
                   max_uses, uses_count, per_user_limit, conditions_json, is_active, valid_from, valid_until,
                   created_by, created_at
            FROM promotions
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [_promotion_to_out(dict(row)) for row in rows]
    return PromotionListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/promotions", response_model=PromotionOut)
def create_promotion(
    payload: PromotionCreateIn,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row_id = str(uuid4())
    data = payload.model_dump(mode="json")
    created_by = str(current_user.id) if current_user and current_user.id else None
    try:
        db.execute(
            text(
                """
                INSERT INTO promotions (
                    id, code, name, type, discount_pct, discount_cents, min_order_cents, max_discount_cents,
                    max_uses, uses_count, per_user_limit, conditions_json, is_active, valid_from, valid_until,
                    created_by, created_at
                ) VALUES (
                    :id, :code, :name, :type, :discount_pct, :discount_cents, :min_order_cents, :max_discount_cents,
                    :max_uses, 0, :per_user_limit, CAST(:conditions_json AS JSONB), TRUE, :valid_from, :valid_until,
                    :created_by, NOW()
                )
                """
            ),
            {"id": row_id, "created_by": created_by, **data, "conditions_json": json.dumps(data.get("conditions_json") or {})},
        )
        _record_pr3_audit(
            db=db,
            correlation_id=corr_id,
            current_user=current_user,
            action="PR3_PROMOTION_CREATE",
            payload={"before": None, "after": {"id": row_id, "created_by": created_by, **data}},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _record_pr3_audit(
            db=db,
            correlation_id=corr_id,
            current_user=current_user,
            action="PR3_PROMOTION_CREATE",
            result="ERROR",
            error_message=str(exc),
            payload={"attempted_after": {"id": row_id, "created_by": created_by, **data}},
        )
        db.commit()
        raise HTTPException(
            status_code=422,
            detail={"type": "PROMOTION_CREATE_FAILED", "message": "Não foi possível criar promoção.", "error": str(exc)},
        ) from exc
    row = db.execute(
        text(
            """
            SELECT id, code, name, type, discount_pct, discount_cents, min_order_cents, max_discount_cents,
                   max_uses, uses_count, per_user_limit, conditions_json, is_active, valid_from, valid_until,
                   created_by, created_at
            FROM promotions
            WHERE id = :id
            """
        ),
        {"id": row_id},
    ).mappings().first()
    return _promotion_to_out(dict(row or {}))


@router.patch("/promotions/{promotion_id}/status", response_model=PromotionStatusOut)
def patch_promotion_status(
    promotion_id: str,
    payload: PromotionStatusPatchIn,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    before_row = db.execute(
        text(
            """
            SELECT id, is_active, valid_from, valid_until
            FROM promotions
            WHERE id = :id
            """
        ),
        {"id": promotion_id},
    ).mappings().first()
    if not before_row:
        raise HTTPException(
            status_code=404,
            detail={"type": "PROMOTION_NOT_FOUND", "message": "Promoção não encontrada.", "promotion_id": promotion_id},
        )
    corr_id = _resolve_correlation_id(correlation_id)
    db.execute(
        text(
            """
            UPDATE promotions
            SET is_active = :is_active
            WHERE id = :id
            """
        ),
        {"id": promotion_id, "is_active": bool(payload.is_active)},
    )
    after_row = db.execute(
        text("SELECT id, is_active FROM promotions WHERE id = :id"),
        {"id": promotion_id},
    ).mappings().first()
    _record_pr3_audit(
        db=db,
        correlation_id=corr_id,
        current_user=current_user,
        action="PR3_PROMOTION_STATUS_PATCH",
        payload={
            "before": dict(before_row),
            "after": dict(after_row or {}),
            "reason": payload.reason,
        },
    )
    db.commit()
    return PromotionStatusOut(
        ok=True,
        promotion_id=promotion_id,
        is_active=bool((after_row or {}).get("is_active")),
        changed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/promotions/validate", response_model=PromotionValidateOut)
def validate_promotion(
    payload: PromotionValidateIn,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    normalized_code = str(payload.promotion_code or "").strip()
    if not normalized_code:
        return PromotionValidateOut(ok=True, valid=False, discount_cents=0, reason="promotion_code obrigatório")
    promo = db.execute(
        text(
            """
            SELECT id, code, type, discount_pct, discount_cents, min_order_cents, max_discount_cents, max_uses, uses_count,
                   is_active, valid_from, valid_until
            FROM promotions
            WHERE code = :code
            """
        ),
        {"code": normalized_code},
    ).mappings().first()
    if not promo:
        return PromotionValidateOut(ok=True, valid=False, discount_cents=0, reason="promoção inexistente")
    if not bool(promo.get("is_active")):
        return PromotionValidateOut(ok=True, valid=False, promotion_id=str(promo.get("id")), promotion_code=normalized_code, discount_cents=0, reason="promoção inativa")
    valid_from = promo.get("valid_from")
    valid_until = promo.get("valid_until")
    if valid_from and valid_from > now:
        return PromotionValidateOut(ok=True, valid=False, promotion_id=str(promo.get("id")), promotion_code=normalized_code, discount_cents=0, reason="promoção ainda não vigente")
    if valid_until and valid_until < now:
        return PromotionValidateOut(ok=True, valid=False, promotion_id=str(promo.get("id")), promotion_code=normalized_code, discount_cents=0, reason="promoção expirada")
    if promo.get("max_uses") is not None and int(promo.get("uses_count") or 0) >= int(promo.get("max_uses") or 0):
        return PromotionValidateOut(ok=True, valid=False, promotion_id=str(promo.get("id")), promotion_code=normalized_code, discount_cents=0, reason="limite de uso atingido")
    total = int(payload.total_amount_cents or 0)
    min_order = int(promo.get("min_order_cents") or 0)
    if total < min_order:
        return PromotionValidateOut(ok=True, valid=False, promotion_id=str(promo.get("id")), promotion_code=normalized_code, discount_cents=0, reason="pedido abaixo do mínimo da promoção")
    discount_cents = 0
    promo_type = str(promo.get("type") or "")
    if promo_type == "PERCENT_OFF":
        pct = float(promo.get("discount_pct") or 0)
        discount_cents = int(round((total * pct) / 100))
    else:
        discount_cents = int(promo.get("discount_cents") or 0)
    max_discount = promo.get("max_discount_cents")
    if max_discount is not None:
        discount_cents = min(discount_cents, int(max_discount))
    discount_cents = max(discount_cents, 0)
    return PromotionValidateOut(
        ok=True,
        valid=True,
        promotion_id=str(promo.get("id")),
        promotion_code=normalized_code,
        discount_cents=discount_cents,
        reason=None,
    )


@router.get("/products/{product_id}/fiscal-config", response_model=ProductFiscalConfigOut)
def get_product_fiscal_config(
    product_id: str,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT sku_id, ncm_code, cest, icms_cst, pis_cst, cofins_cst, iva_category, is_active,
                   unit_of_measure, origin_type, cfop, tax_rate_pct, is_service, updated_at
            FROM product_fiscal_config
            WHERE sku_id = :sku_id
            """
        ),
        {"sku_id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_FISCAL_CONFIG_NOT_FOUND", "message": "Config fiscal não encontrada para o produto.", "product_id": product_id},
        )
    return ProductFiscalConfigOut(
        sku_id=str(row.get("sku_id") or ""),
        ncm_code=(str(row.get("ncm_code")) if row.get("ncm_code") is not None else None),
        cest=(str(row.get("cest")) if row.get("cest") is not None else None),
        icms_cst=(str(row.get("icms_cst")) if row.get("icms_cst") is not None else None),
        pis_cst=(str(row.get("pis_cst")) if row.get("pis_cst") is not None else None),
        cofins_cst=(str(row.get("cofins_cst")) if row.get("cofins_cst") is not None else None),
        iva_category=(str(row.get("iva_category")) if row.get("iva_category") is not None else None),
        is_active=bool(row.get("is_active")),
        unit_of_measure=str(row.get("unit_of_measure") or "UN"),
        origin_type=str(row.get("origin_type") or "0"),
        cfop=(str(row.get("cfop")) if row.get("cfop") is not None else None),
        tax_rate_pct=(float(row.get("tax_rate_pct")) if row.get("tax_rate_pct") is not None else None),
        is_service=bool(row.get("is_service")),
        updated_at=_to_iso_utc(row.get("updated_at")) if row.get("updated_at") else None,
    )


@router.put("/products/{product_id}/fiscal-config", response_model=ProductFiscalConfigUpsertOut)
def put_product_fiscal_config(
    product_id: str,
    payload: ProductFiscalConfigUpsertIn,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product_exists = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).mappings().first()
    if not product_exists:
        raise HTTPException(
            status_code=404,
            detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado.", "product_id": product_id},
        )
    before_row = db.execute(
        text(
            """
            SELECT sku_id, ncm_code, cest, icms_cst, pis_cst, cofins_cst, iva_category, is_active,
                   unit_of_measure, origin_type, cfop, tax_rate_pct, is_service, updated_at
            FROM product_fiscal_config
            WHERE sku_id = :sku_id
            """
        ),
        {"sku_id": product_id},
    ).mappings().first()
    corr_id = _resolve_correlation_id(correlation_id)
    data = payload.model_dump(mode="json")
    db.execute(
        text(
            """
            INSERT INTO product_fiscal_config (
                sku_id, ncm_code, cest, icms_cst, pis_cst, cofins_cst, iva_category, is_active,
                unit_of_measure, origin_type, cfop, tax_rate_pct, is_service, updated_at
            ) VALUES (
                :sku_id, :ncm_code, :cest, :icms_cst, :pis_cst, :cofins_cst, :iva_category, :is_active,
                :unit_of_measure, :origin_type, :cfop, :tax_rate_pct, :is_service, NOW()
            )
            ON CONFLICT (sku_id) DO UPDATE SET
                ncm_code = EXCLUDED.ncm_code,
                cest = EXCLUDED.cest,
                icms_cst = EXCLUDED.icms_cst,
                pis_cst = EXCLUDED.pis_cst,
                cofins_cst = EXCLUDED.cofins_cst,
                iva_category = EXCLUDED.iva_category,
                is_active = EXCLUDED.is_active,
                unit_of_measure = EXCLUDED.unit_of_measure,
                origin_type = EXCLUDED.origin_type,
                cfop = EXCLUDED.cfop,
                tax_rate_pct = EXCLUDED.tax_rate_pct,
                is_service = EXCLUDED.is_service,
                updated_at = NOW()
            """
        ),
        {"sku_id": product_id, **data},
    )
    after_row = db.execute(
        text(
            """
            SELECT sku_id, ncm_code, cest, icms_cst, pis_cst, cofins_cst, iva_category, is_active,
                   unit_of_measure, origin_type, cfop, tax_rate_pct, is_service, updated_at
            FROM product_fiscal_config
            WHERE sku_id = :sku_id
            """
        ),
        {"sku_id": product_id},
    ).mappings().first()
    _record_pr3_audit(
        db=db,
        correlation_id=corr_id,
        current_user=current_user,
        action="PR3_PRODUCT_FISCAL_CONFIG_UPSERT",
        payload={
            "product_id": product_id,
            "before": dict(before_row) if before_row else None,
            "after": dict(after_row) if after_row else None,
        },
    )
    db.commit()
    return ProductFiscalConfigUpsertOut(
        ok=True,
        config=ProductFiscalConfigOut(
            sku_id=str(after_row.get("sku_id") or ""),
            ncm_code=(str(after_row.get("ncm_code")) if after_row.get("ncm_code") is not None else None),
            cest=(str(after_row.get("cest")) if after_row.get("cest") is not None else None),
            icms_cst=(str(after_row.get("icms_cst")) if after_row.get("icms_cst") is not None else None),
            pis_cst=(str(after_row.get("pis_cst")) if after_row.get("pis_cst") is not None else None),
            cofins_cst=(str(after_row.get("cofins_cst")) if after_row.get("cofins_cst") is not None else None),
            iva_category=(str(after_row.get("iva_category")) if after_row.get("iva_category") is not None else None),
            is_active=bool(after_row.get("is_active")),
            unit_of_measure=str(after_row.get("unit_of_measure") or "UN"),
            origin_type=str(after_row.get("origin_type") or "0"),
            cfop=(str(after_row.get("cfop")) if after_row.get("cfop") is not None else None),
            tax_rate_pct=(float(after_row.get("tax_rate_pct")) if after_row.get("tax_rate_pct") is not None else None),
            is_service=bool(after_row.get("is_service")),
            updated_at=_to_iso_utc(after_row.get("updated_at")) if after_row.get("updated_at") else None,
        ),
    )


@router.get("/fiscal/auto-classification-log", response_model=FiscalAutoClassificationLogListOut)
def list_fiscal_auto_classification_log(
    order_id: str | None = Query(default=None),
    sku_id: str | None = Query(default=None),
    source: str | None = Query(default=None),
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from")
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )
    where_parts = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    normalized_order_id = str(order_id or "").strip()
    normalized_sku_id = str(sku_id or "").strip()
    normalized_source = str(source or "").strip().upper()
    if normalized_order_id:
        where_parts.append("order_id = :order_id")
        params["order_id"] = normalized_order_id
    if normalized_sku_id:
        where_parts.append("sku_id = :sku_id")
        params["sku_id"] = normalized_sku_id
    if normalized_source:
        where_parts.append("source = :source")
        params["source"] = normalized_source
    if dt_from is not None:
        where_parts.append("classified_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("classified_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)
    total_row = db.execute(
        text(f"SELECT COUNT(*) AS total FROM fiscal_auto_classification_log WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT id, order_id, invoice_id, sku_id, ncm_applied, icms_cst_applied, pis_cst_applied,
                   cofins_cst_applied, cfop_applied, source, classified_at
            FROM fiscal_auto_classification_log
            WHERE {where_sql}
            ORDER BY classified_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [
        FiscalAutoClassificationLogItemOut(
            id=int(row.get("id") or 0),
            order_id=str(row.get("order_id") or ""),
            invoice_id=(str(row.get("invoice_id")) if row.get("invoice_id") is not None else None),
            sku_id=str(row.get("sku_id") or ""),
            ncm_applied=(str(row.get("ncm_applied")) if row.get("ncm_applied") is not None else None),
            icms_cst_applied=(str(row.get("icms_cst_applied")) if row.get("icms_cst_applied") is not None else None),
            pis_cst_applied=(str(row.get("pis_cst_applied")) if row.get("pis_cst_applied") is not None else None),
            cofins_cst_applied=(str(row.get("cofins_cst_applied")) if row.get("cofins_cst_applied") is not None else None),
            cfop_applied=(str(row.get("cfop_applied")) if row.get("cfop_applied") is not None else None),
            source=str(row.get("source") or ""),
            classified_at=_to_iso_utc(row.get("classified_at")),
        )
        for row in rows
    ]
    return FiscalAutoClassificationLogListOut(
        ok=True,
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )

