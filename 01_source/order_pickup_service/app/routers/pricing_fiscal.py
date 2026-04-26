from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.user import User
from app.schemas.pricing_fiscal import (
    FiscalAutoClassificationLogItemOut,
    FiscalAutoClassificationLogListOut,
    FiscalAutoClassificationReprocessOut,
    PricingFiscalBadgeOut,
    PricingFiscalDefaultAlertItemOut,
    PricingFiscalDefaultAlertsOut,
    PricingFiscalOverviewKpiOut,
    PricingFiscalOverviewOut,
    PricingFiscalOverviewTopItemOut,
    PricingFiscalSourceSummaryItemOut,
    PricingFiscalSourceSummaryOut,
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
from app.services.fiscal_context_service import build_fiscal_context
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


def _safe_delta_pct(current: int, previous: int) -> float:
    if previous <= 0:
        if current <= 0:
            return 0.0
        return 100.0
    return round(((current - previous) / previous) * 100, 2)


def _resolve_trend(current: int, previous: int) -> str:
    if current > previous:
        return "up"
    if current < previous:
        return "down"
    return "stable"


def _resolve_confidence_and_note(*, total_current: int, total_previous: int) -> tuple[str, str]:
    min_volume = min(int(total_current or 0), int(total_previous or 0))
    if min_volume < 10:
        return (
            "LOW",
            "Base de eventos muito pequena no período comparado; variações percentuais podem oscilar bastante.",
        )
    if min_volume < 30:
        return (
            "MEDIUM",
            "Base de eventos moderada; use a variação percentual junto com os valores absolutos.",
        )
    return (
        "HIGH",
        "Base de eventos suficiente para leitura mais estável das tendências percentuais.",
    )


def _resolve_confidence_badge(confidence_level: str) -> PricingFiscalBadgeOut:
    level = str(confidence_level or "").upper()
    if level == "LOW":
        return PricingFiscalBadgeOut(
            key="confidence_low",
            label="Confianca baixa",
            color="#DC2626",
            icon="alert-triangle",
        )
    if level == "MEDIUM":
        return PricingFiscalBadgeOut(
            key="confidence_medium",
            label="Confianca moderada",
            color="#D97706",
            icon="alert-circle",
        )
    return PricingFiscalBadgeOut(
        key="confidence_high",
        label="Confianca alta",
        color="#16A34A",
        icon="check-circle",
    )


def _to_int(value, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_validate_out_from_audit(details: dict) -> PromotionValidateOut | None:
    payload = _json_load_dict(details.get("after"), default={}) if isinstance(details, dict) else {}
    if not payload:
        return None
    return PromotionValidateOut(
        ok=bool(payload.get("ok", True)),
        valid=bool(payload.get("valid", False)),
        idempotent=True,
        promotion_id=(str(payload.get("promotion_id")) if payload.get("promotion_id") is not None else None),
        promotion_code=(str(payload.get("promotion_code")) if payload.get("promotion_code") is not None else None),
        discount_cents=_to_int(payload.get("discount_cents"), 0),
        reason=(str(payload.get("reason")) if payload.get("reason") is not None else None),
    )


def _compute_advanced_discount(
    *,
    promo_type: str,
    total_amount_cents: int,
    discount_pct: float | None,
    discount_cents: int | None,
    max_discount_cents: int | None,
    conditions_json: dict,
    items: list[dict],
) -> int:
    normalized_type = str(promo_type or "").strip().upper()
    item_quantities = [max(_to_int(item.get("quantity"), 1), 1) for item in (items or [])]
    item_unit_prices = [max(_to_int(item.get("unit_price_cents"), 0), 0) for item in (items or [])]
    total_qty = sum(item_quantities)
    fallback_unit_price = min(item_unit_prices) if item_unit_prices else 0

    resolved_discount = 0
    if normalized_type == "PERCENT_OFF":
        pct = float(discount_pct or 0)
        resolved_discount = int(round((total_amount_cents * pct) / 100))
    elif normalized_type == "FIXED_OFF":
        resolved_discount = max(_to_int(discount_cents, 0), 0)
    elif normalized_type == "BUY_X_GET_Y":
        buy_qty = max(_to_int(conditions_json.get("buy_qty"), 1), 1)
        get_qty = max(_to_int(conditions_json.get("get_qty"), 1), 1)
        group_size = buy_qty + get_qty
        if total_qty < group_size:
            return 0
        free_unit_price = max(_to_int(conditions_json.get("free_item_price_cents"), fallback_unit_price), 0)
        eligible_groups = total_qty // group_size
        resolved_discount = eligible_groups * get_qty * free_unit_price
    elif normalized_type == "FREE_ITEM":
        free_qty = max(_to_int(conditions_json.get("free_qty"), 1), 1)
        free_unit_price = max(_to_int(conditions_json.get("free_item_price_cents"), fallback_unit_price), 0)
        resolved_discount = free_qty * free_unit_price
    elif normalized_type == "BUNDLE_DISCOUNT":
        bundle_size = max(_to_int(conditions_json.get("bundle_size"), 1), 1)
        bundle_price_cents = max(_to_int(conditions_json.get("bundle_price_cents"), 0), 0)
        if not item_unit_prices:
            return 0
        expanded_prices: list[int] = []
        for idx, unit_price in enumerate(item_unit_prices):
            qty = item_quantities[idx] if idx < len(item_quantities) else 1
            expanded_prices.extend([unit_price] * qty)
        if len(expanded_prices) < bundle_size:
            return 0
        expanded_prices.sort(reverse=True)
        eligible_sets = len(expanded_prices) // bundle_size
        for set_idx in range(eligible_sets):
            slice_start = set_idx * bundle_size
            slice_end = slice_start + bundle_size
            group_total = sum(expanded_prices[slice_start:slice_end])
            resolved_discount += max(group_total - bundle_price_cents, 0)
    else:
        resolved_discount = max(_to_int(discount_cents, 0), 0)

    if max_discount_cents is not None:
        resolved_discount = min(resolved_discount, max(_to_int(max_discount_cents, 0), 0))
    return max(resolved_discount, 0)


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
                    created_by, created_at, updated_at
                ) VALUES (
                    :id, :code, :name, :type, :discount_pct, :discount_cents, :min_order_cents, :max_discount_cents,
                    :max_uses, 0, :per_user_limit, CAST(:conditions_json AS JSONB), TRUE, :valid_from, :valid_until,
                    :created_by, NOW(), NOW()
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
            SELECT id, is_active, valid_from, valid_until, updated_at
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
            SET is_active = :is_active,
                updated_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": promotion_id, "is_active": bool(payload.is_active)},
    )
    after_row = db.execute(
        text("SELECT id, is_active, updated_at FROM promotions WHERE id = :id"),
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
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    now = datetime.now(timezone.utc)
    normalized_code = str(payload.promotion_code or "").strip()
    normalized_order_id = str(payload.order_id or "").strip()
    promotion_type: str | None = None

    existing_validation = db.execute(
        text(
            """
            SELECT details_json
            FROM ops_action_audit
            WHERE action = 'PR3_PROMOTION_VALIDATE'
              AND order_id = :order_id
              AND (
                    (details_json::jsonb)->>'promotion_code' = :promotion_code
                    OR (details_json::jsonb)->'after'->>'promotion_code' = :promotion_code
              )
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"order_id": normalized_order_id, "promotion_code": normalized_code},
    ).mappings().first()
    if existing_validation:
        idempotent_response = _build_validate_out_from_audit(_json_load_dict(existing_validation.get("details_json"), default={}))
        if idempotent_response is not None:
            _record_pr3_audit(
                db=db,
                correlation_id=corr_id,
                current_user=current_user,
                action="PR3_PROMOTION_VALIDATE_IDEMPOTENT_HIT",
                order_id=normalized_order_id,
                payload={
                    "before": None,
                    "after": idempotent_response.model_dump(mode="json"),
                    "promotion_code": normalized_code or None,
                },
            )
            db.commit()
            return idempotent_response

    response: PromotionValidateOut
    if not normalized_code:
        response = PromotionValidateOut(ok=True, valid=False, idempotent=False, discount_cents=0, reason="promotion_code obrigatório")
    else:
        promo = db.execute(
            text(
                """
                SELECT id, code, type, discount_pct, discount_cents, min_order_cents, max_discount_cents, max_uses, uses_count,
                       is_active, valid_from, valid_until, conditions_json
                FROM promotions
                WHERE code = :code
                """
            ),
            {"code": normalized_code},
        ).mappings().first()
        if not promo:
            response = PromotionValidateOut(ok=True, valid=False, idempotent=False, discount_cents=0, reason="promoção inexistente")
        elif not bool(promo.get("is_active")):
            promotion_type = str(promo.get("type") or "")
            response = PromotionValidateOut(
                ok=True,
                valid=False,
                idempotent=False,
                promotion_id=str(promo.get("id")),
                promotion_code=normalized_code,
                discount_cents=0,
                reason="promoção inativa",
            )
        else:
            valid_from = promo.get("valid_from")
            valid_until = promo.get("valid_until")
            promotion_type = str(promo.get("type") or "")
            if valid_from and valid_from > now:
                response = PromotionValidateOut(
                    ok=True,
                    valid=False,
                    idempotent=False,
                    promotion_id=str(promo.get("id")),
                    promotion_code=normalized_code,
                    discount_cents=0,
                    reason="promoção ainda não vigente",
                )
            elif valid_until and valid_until < now:
                response = PromotionValidateOut(
                    ok=True,
                    valid=False,
                    idempotent=False,
                    promotion_id=str(promo.get("id")),
                    promotion_code=normalized_code,
                    discount_cents=0,
                    reason="promoção expirada",
                )
            elif promo.get("max_uses") is not None and int(promo.get("uses_count") or 0) >= int(promo.get("max_uses") or 0):
                response = PromotionValidateOut(
                    ok=True,
                    valid=False,
                    idempotent=False,
                    promotion_id=str(promo.get("id")),
                    promotion_code=normalized_code,
                    discount_cents=0,
                    reason="limite de uso atingido",
                )
            else:
                total = int(payload.total_amount_cents or 0)
                min_order = int(promo.get("min_order_cents") or 0)
                if total < min_order:
                    response = PromotionValidateOut(
                        ok=True,
                        valid=False,
                        idempotent=False,
                        promotion_id=str(promo.get("id")),
                        promotion_code=normalized_code,
                        discount_cents=0,
                        reason="pedido abaixo do mínimo da promoção",
                    )
                else:
                    discount_cents = _compute_advanced_discount(
                        promo_type=str(promo.get("type") or ""),
                        total_amount_cents=total,
                        discount_pct=(float(promo.get("discount_pct")) if promo.get("discount_pct") is not None else None),
                        discount_cents=(int(promo.get("discount_cents")) if promo.get("discount_cents") is not None else None),
                        max_discount_cents=(int(promo.get("max_discount_cents")) if promo.get("max_discount_cents") is not None else None),
                        conditions_json=_json_load_dict(promo.get("conditions_json"), default={}),
                        items=payload.items or [],
                    )
                    response = PromotionValidateOut(
                        ok=True,
                        valid=True,
                        idempotent=False,
                        promotion_id=str(promo.get("id")),
                        promotion_code=normalized_code,
                        discount_cents=discount_cents,
                        reason=None,
                    )

    _record_pr3_audit(
        db=db,
        correlation_id=corr_id,
        current_user=current_user,
        action="PR3_PROMOTION_VALIDATE",
        order_id=normalized_order_id,
        payload={
            "before": None,
            "after": response.model_dump(mode="json"),
            "promotion_code": normalized_code or None,
            "promotion_type": promotion_type,
        },
    )
    db.commit()
    return response


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


@router.get("/fiscal/auto-classification-log/{order_id}", response_model=FiscalAutoClassificationLogListOut)
def list_fiscal_auto_classification_log_by_order(
    order_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    normalized_order_id = str(order_id or "").strip()
    if not normalized_order_id:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_ORDER_ID", "message": "order_id obrigatório."},
        )
    total_row = db.execute(
        text("SELECT COUNT(*) AS total FROM fiscal_auto_classification_log WHERE order_id = :order_id"),
        {"order_id": normalized_order_id},
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            """
            SELECT id, order_id, invoice_id, sku_id, ncm_applied, icms_cst_applied, pis_cst_applied,
                   cofins_cst_applied, cfop_applied, source, classified_at
            FROM fiscal_auto_classification_log
            WHERE order_id = :order_id
            ORDER BY classified_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"order_id": normalized_order_id, "limit": int(limit), "offset": int(offset)},
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
    return FiscalAutoClassificationLogListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/fiscal/auto-classification/{order_id}/reprocess", response_model=FiscalAutoClassificationReprocessOut)
def reprocess_fiscal_auto_classification(
    order_id: str,
    db: Session = Depends(get_db),
):
    normalized_order_id = str(order_id or "").strip()
    if not normalized_order_id:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_ORDER_ID", "message": "order_id obrigatório."},
        )
    order_exists = db.execute(
        text("SELECT id FROM orders WHERE id = :order_id"),
        {"order_id": normalized_order_id},
    ).mappings().first()
    if not order_exists:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_NOT_FOUND", "message": "Pedido não encontrado.", "order_id": normalized_order_id},
        )
    # Reprocessa de forma determinística removendo logs anteriores desse pedido.
    db.execute(
        text("DELETE FROM fiscal_auto_classification_log WHERE order_id = :order_id"),
        {"order_id": normalized_order_id},
    )
    db.commit()
    ctx = build_fiscal_context(db, normalized_order_id)
    rows = db.execute(
        text(
            """
            SELECT source
            FROM fiscal_auto_classification_log
            WHERE order_id = :order_id
            """
        ),
        {"order_id": normalized_order_id},
    ).mappings().all()
    sources = sorted({str(row.get("source") or "") for row in rows if str(row.get("source") or "").strip()})
    return FiscalAutoClassificationReprocessOut(
        ok=True,
        order_id=normalized_order_id,
        rebuilt=True,
        total_items=len(list(ctx.get("items") or [])),
        total_log_rows=len(rows),
        sources=sources,
    )


@router.get("/ops/products/pricing-fiscal/overview", response_model=PricingFiscalOverviewOut)
def get_ops_pricing_fiscal_overview(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    top_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or now
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (
        dt_to - timedelta(hours=24)
    )
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    window_seconds = max(int((dt_to - dt_from).total_seconds()), 1)
    previous_to = dt_from
    previous_from = dt_from - timedelta(seconds=window_seconds)

    bundle_current_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action IN ('PR3_BUNDLE_CREATE', 'PR3_BUNDLE_ITEM_ADD')
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"from": dt_from, "to": dt_to},
    ).mappings().first()
    bundle_previous_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action IN ('PR3_BUNDLE_CREATE', 'PR3_BUNDLE_ITEM_ADD')
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"from": previous_from, "to": previous_to},
    ).mappings().first()
    bundle_current = int((bundle_current_row or {}).get("total") or 0)
    bundle_previous = int((bundle_previous_row or {}).get("total") or 0)

    promo_current_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action = 'PR3_PROMOTION_VALIDATE'
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"from": dt_from, "to": dt_to},
    ).mappings().first()
    promo_previous_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action = 'PR3_PROMOTION_VALIDATE'
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"from": previous_from, "to": previous_to},
    ).mappings().first()
    promo_current = int((promo_current_row or {}).get("total") or 0)
    promo_previous = int((promo_previous_row or {}).get("total") or 0)

    fiscal_current_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE classified_at >= :from
              AND classified_at <= :to
            """
        ),
        {"from": dt_from, "to": dt_to},
    ).mappings().first()
    fiscal_previous_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE classified_at >= :from
              AND classified_at <= :to
            """
        ),
        {"from": previous_from, "to": previous_to},
    ).mappings().first()
    fiscal_current = int((fiscal_current_row or {}).get("total") or 0)
    fiscal_previous = int((fiscal_previous_row or {}).get("total") or 0)

    default_current_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE source = 'DEFAULT'
              AND classified_at >= :from
              AND classified_at <= :to
            """
        ),
        {"from": dt_from, "to": dt_to},
    ).mappings().first()
    default_previous_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE source = 'DEFAULT'
              AND classified_at >= :from
              AND classified_at <= :to
            """
        ),
        {"from": previous_from, "to": previous_to},
    ).mappings().first()
    default_current = int((default_current_row or {}).get("total") or 0)
    default_previous = int((default_previous_row or {}).get("total") or 0)

    overall_current = bundle_current + promo_current + fiscal_current
    overall_previous = bundle_previous + promo_previous + fiscal_previous
    confidence_level, confidence_note = _resolve_confidence_and_note(
        total_current=overall_current,
        total_previous=overall_previous,
    )

    kpis = [
        PricingFiscalOverviewKpiOut(
            key="bundle_events",
            label="Eventos de bundles",
            current=bundle_current,
            previous=bundle_previous,
            delta_pct=_safe_delta_pct(bundle_current, bundle_previous),
            trend=_resolve_trend(bundle_current, bundle_previous),
        ),
        PricingFiscalOverviewKpiOut(
            key="promotion_validations",
            label="Validações de promoção",
            current=promo_current,
            previous=promo_previous,
            delta_pct=_safe_delta_pct(promo_current, promo_previous),
            trend=_resolve_trend(promo_current, promo_previous),
        ),
        PricingFiscalOverviewKpiOut(
            key="fiscal_classifications",
            label="Classificações fiscais",
            current=fiscal_current,
            previous=fiscal_previous,
            delta_pct=_safe_delta_pct(fiscal_current, fiscal_previous),
            trend=_resolve_trend(fiscal_current, fiscal_previous),
        ),
        PricingFiscalOverviewKpiOut(
            key="default_classifications",
            label="Classificações em DEFAULT",
            current=default_current,
            previous=default_previous,
            delta_pct=_safe_delta_pct(default_current, default_previous),
            trend=_resolve_trend(default_current, default_previous),
        ),
    ]

    promo_rows = db.execute(
        text(
            """
            SELECT
                CASE
                    WHEN created_at >= :current_from AND created_at <= :current_to THEN 'current'
                    ELSE 'previous'
                END AS bucket,
                COALESCE(
                    (details_json::jsonb)->>'promotion_code',
                    (details_json::jsonb)->'after'->>'promotion_code',
                    '__none__'
                ) AS promotion_code,
                COUNT(*) AS total
            FROM ops_action_audit
            WHERE action = 'PR3_PROMOTION_VALIDATE'
              AND created_at >= :previous_from
              AND created_at <= :current_to
            GROUP BY bucket, promotion_code
            """
        ),
        {
            "current_from": dt_from,
            "current_to": dt_to,
            "previous_from": previous_from,
        },
    ).mappings().all()
    promo_counter_current: Counter[str] = Counter()
    promo_counter_previous: Counter[str] = Counter()
    for row in promo_rows:
        code = str(row.get("promotion_code") or "__none__")
        bucket = str(row.get("bucket") or "previous")
        total = int(row.get("total") or 0)
        if bucket == "current":
            promo_counter_current[code] += total
        else:
            promo_counter_previous[code] += total

    default_sku_rows = db.execute(
        text(
            """
            SELECT
                CASE
                    WHEN classified_at >= :current_from AND classified_at <= :current_to THEN 'current'
                    ELSE 'previous'
                END AS bucket,
                sku_id,
                COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE source = 'DEFAULT'
              AND classified_at >= :previous_from
              AND classified_at <= :current_to
            GROUP BY bucket, sku_id
            """
        ),
        {
            "current_from": dt_from,
            "current_to": dt_to,
            "previous_from": previous_from,
        },
    ).mappings().all()
    default_sku_current: Counter[str] = Counter()
    default_sku_previous: Counter[str] = Counter()
    for row in default_sku_rows:
        sku = str(row.get("sku_id") or "__unknown__")
        bucket = str(row.get("bucket") or "previous")
        total = int(row.get("total") or 0)
        if bucket == "current":
            default_sku_current[sku] += total
        else:
            default_sku_previous[sku] += total

    source_rows = db.execute(
        text(
            """
            SELECT
                CASE
                    WHEN classified_at >= :current_from AND classified_at <= :current_to THEN 'current'
                    ELSE 'previous'
                END AS bucket,
                source,
                COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE classified_at >= :previous_from
              AND classified_at <= :current_to
            GROUP BY bucket, source
            """
        ),
        {
            "current_from": dt_from,
            "current_to": dt_to,
            "previous_from": previous_from,
        },
    ).mappings().all()
    source_current: Counter[str] = Counter()
    source_previous: Counter[str] = Counter()
    for row in source_rows:
        source_key = str(row.get("source") or "__unknown__")
        bucket = str(row.get("bucket") or "previous")
        total = int(row.get("total") or 0)
        if bucket == "current":
            source_current[source_key] += total
        else:
            source_previous[source_key] += total

    def build_top(counter_current: Counter[str], counter_previous: Counter[str], *, fallback_label: str) -> list[PricingFiscalOverviewTopItemOut]:
        keys = sorted(counter_current.keys(), key=lambda key: (-counter_current[key], key))
        result: list[PricingFiscalOverviewTopItemOut] = []
        for key in keys[:top_limit]:
            current_value = int(counter_current.get(key, 0))
            previous_value = int(counter_previous.get(key, 0))
            label = key if key not in {"__none__", "__unknown__"} else fallback_label
            result.append(
                PricingFiscalOverviewTopItemOut(
                    key=key,
                    label=label,
                    current=current_value,
                    previous=previous_value,
                    delta_pct=_safe_delta_pct(current_value, previous_value),
                    trend=_resolve_trend(current_value, previous_value),
                )
            )
        return result

    return PricingFiscalOverviewOut(
        ok=True,
        period_from=_to_iso_utc(dt_from),
        period_to=_to_iso_utc(dt_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        comparison=PricingFiscalOverviewKpiOut(
            key="total_events",
            label="Eventos totais Pr-3",
            current=overall_current,
            previous=overall_previous,
            delta_pct=_safe_delta_pct(overall_current, overall_previous),
            trend=_resolve_trend(overall_current, overall_previous),
        ),
        confidence_level=confidence_level,
        confidence_note=confidence_note,
        confidence_badge=_resolve_confidence_badge(confidence_level),
        kpis=kpis,
        tops_promotion_codes=build_top(
            promo_counter_current,
            promo_counter_previous,
            fallback_label="Sem codigo",
        ),
        tops_default_skus=build_top(
            default_sku_current,
            default_sku_previous,
            fallback_label="SKU desconhecido",
        ),
        tops_fiscal_source=build_top(
            source_current,
            source_previous,
            fallback_label="Fonte desconhecida",
        ),
    )


@router.get("/ops/products/pricing-fiscal/classification-sources", response_model=PricingFiscalSourceSummaryOut)
def get_ops_pricing_fiscal_classification_sources(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or now
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (
        dt_to - timedelta(hours=24)
    )
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    window_seconds = max(int((dt_to - dt_from).total_seconds()), 1)
    previous_to = dt_from
    previous_from = dt_from - timedelta(seconds=window_seconds)

    rows = db.execute(
        text(
            """
            SELECT
                CASE
                    WHEN classified_at >= :current_from AND classified_at <= :current_to THEN 'current'
                    ELSE 'previous'
                END AS bucket,
                source,
                COUNT(*) AS total
            FROM fiscal_auto_classification_log
            WHERE classified_at >= :previous_from
              AND classified_at <= :current_to
            GROUP BY bucket, source
            """
        ),
        {
            "current_from": dt_from,
            "current_to": dt_to,
            "previous_from": previous_from,
        },
    ).mappings().all()

    current_counter: Counter[str] = Counter()
    previous_counter: Counter[str] = Counter()
    for row in rows:
        bucket = str(row.get("bucket") or "previous")
        source = str(row.get("source") or "UNKNOWN")
        total = int(row.get("total") or 0)
        if bucket == "current":
            current_counter[source] += total
        else:
            previous_counter[source] += total

    all_sources = sorted(set(current_counter.keys()) | set(previous_counter.keys()))
    items = [
        PricingFiscalSourceSummaryItemOut(
            source=source,
            current=int(current_counter.get(source, 0)),
            previous=int(previous_counter.get(source, 0)),
            delta_pct=_safe_delta_pct(int(current_counter.get(source, 0)), int(previous_counter.get(source, 0))),
            trend=_resolve_trend(int(current_counter.get(source, 0)), int(previous_counter.get(source, 0))),
        )
        for source in all_sources
    ]
    items.sort(key=lambda row: (-row.current, row.source))

    total_current = sum(current_counter.values())
    total_previous = sum(previous_counter.values())
    confidence_level, confidence_note = _resolve_confidence_and_note(
        total_current=total_current,
        total_previous=total_previous,
    )

    return PricingFiscalSourceSummaryOut(
        ok=True,
        period_from=_to_iso_utc(dt_from),
        period_to=_to_iso_utc(dt_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        total_current=int(total_current),
        total_previous=int(total_previous),
        confidence_level=confidence_level,
        confidence_note=confidence_note,
        confidence_badge=_resolve_confidence_badge(confidence_level),
        items=items,
    )


@router.get("/ops/products/pricing-fiscal/default-alerts", response_model=PricingFiscalDefaultAlertsOut)
def get_ops_pricing_fiscal_default_alerts(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or now
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (
        dt_to - timedelta(hours=24)
    )
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    window_seconds = max(int((dt_to - dt_from).total_seconds()), 1)
    previous_to = dt_from
    previous_from = dt_from - timedelta(seconds=window_seconds)

    action_name = "PR3_FISCAL_CLASSIFICATION_DEFAULT_ALERT"
    current_total_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action = :action
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"action": action_name, "from": dt_from, "to": dt_to},
    ).mappings().first()
    previous_total_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM ops_action_audit
            WHERE action = :action
              AND created_at >= :from
              AND created_at <= :to
            """
        ),
        {"action": action_name, "from": previous_from, "to": previous_to},
    ).mappings().first()
    total_current = int((current_total_row or {}).get("total") or 0)
    total_previous = int((previous_total_row or {}).get("total") or 0)

    rows = db.execute(
        text(
            """
            SELECT created_at, order_id, correlation_id, details_json
            FROM ops_action_audit
            WHERE action = :action
              AND created_at >= :from
              AND created_at <= :to
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {
            "action": action_name,
            "from": dt_from,
            "to": dt_to,
            "limit": int(limit),
            "offset": int(offset),
        },
    ).mappings().all()
    items = []
    for row in rows:
        details = _json_load_dict(row.get("details_json"), default={})
        items.append(
            PricingFiscalDefaultAlertItemOut(
                created_at=_to_iso_utc(row.get("created_at")),
                order_id=(str(row.get("order_id")) if row.get("order_id") is not None else None),
                sku_id=(str(details.get("sku_id")) if details.get("sku_id") is not None else None),
                source=(str(details.get("source")) if details.get("source") is not None else None),
                message=(str(details.get("message")) if details.get("message") is not None else None),
                correlation_id=str(row.get("correlation_id") or ""),
            )
        )

    confidence_level, confidence_note = _resolve_confidence_and_note(
        total_current=total_current,
        total_previous=total_previous,
    )
    return PricingFiscalDefaultAlertsOut(
        ok=True,
        period_from=_to_iso_utc(dt_from),
        period_to=_to_iso_utc(dt_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        total_current=total_current,
        total_previous=total_previous,
        delta_pct=_safe_delta_pct(total_current, total_previous),
        trend=_resolve_trend(total_current, total_previous),
        confidence_level=confidence_level,
        confidence_note=confidence_note,
        confidence_badge=_resolve_confidence_badge(confidence_level),
        limit=int(limit),
        offset=int(offset),
        items=items,
    )


@router.get("/ops/products/pricing-fiscal/view", response_class=HTMLResponse)
def get_ops_pricing_fiscal_view() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>ELLAN LAB OPS Pricing & Fiscal</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 24px; background:#F8FAFC; color:#0F172A; }
      h1 { margin: 0 0 14px 0; font-size: 24px; }
      .row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 12px; }
      input, button { padding:8px 10px; border:1px solid #CBD5E1; border-radius:8px; background:#fff; }
      button { background:#0F766E; color:#fff; border:none; cursor:pointer; }
      .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 16px 0; }
      .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:12px; }
      .label { color:#475569; font-size:12px; text-transform: uppercase; letter-spacing: .04em; }
      .value { font-size:24px; font-weight:700; margin-top:6px; }
      .muted { color:#64748B; font-size:12px; margin: 8px 0 14px; }
      ul { margin: 0; padding-left: 18px; }
      li { margin-bottom: 6px; font-size: 13px; }
      pre { background:#0B1220; color:#E2E8F0; border-radius:12px; padding:12px; overflow:auto; font-size:12px; }
    </style>
  </head>
  <body>
    <h1>OPS Pricing & Fiscal (Pr-3)</h1>
    <div class="row">
      <input id="from" placeholder="period_from ISO-8601 opcional" size="30" />
      <input id="to" placeholder="period_to ISO-8601 opcional" size="30" />
      <input id="topLimit" placeholder="top_limit (1-20)" value="5" size="16" />
      <button onclick="loadData()">Atualizar</button>
    </div>
    <div class="muted">Endpoint: /ops/products/pricing-fiscal/overview</div>

    <div class="cards">
      <div class="card"><div class="label">Eventos totais</div><div id="kpiTotal" class="value">-</div></div>
      <div class="card"><div class="label">Delta total %</div><div id="kpiDelta" class="value">-</div></div>
      <div class="card"><div class="label">Confidence</div><div id="kpiConfidence" class="value">-</div></div>
      <div class="card"><div class="label">Default atual</div><div id="kpiDefault" class="value">-</div></div>
    </div>

    <div class="cards">
      <div class="card">
        <div class="label">Top promotion codes</div>
        <ul id="topPromotions"><li>-</li></ul>
      </div>
      <div class="card">
        <div class="label">Top SKUs DEFAULT</div>
        <ul id="topSkus"><li>-</li></ul>
      </div>
      <div class="card">
        <div class="label">Top fiscal source</div>
        <ul id="topSource"><li>-</li></ul>
      </div>
    </div>

    <pre id="payload">Carregando...</pre>
    <script>
      function renderTopList(elementId, items) {
        const el = document.getElementById(elementId);
        const list = Array.isArray(items) ? items : [];
        if (!list.length) {
          el.innerHTML = '<li>Sem dados na janela.</li>';
          return;
        }
        el.innerHTML = list
          .map((item) => {
            const trend = String(item?.trend || 'stable').toUpperCase();
            const delta = Number(item?.delta_pct ?? 0).toFixed(2);
            return `<li><strong>${item?.label ?? '-'}</strong> · atual ${item?.current ?? 0} | anterior ${item?.previous ?? 0} | ${delta}% (${trend})</li>`;
          })
          .join('');
      }

      async function loadData() {
        const params = new URLSearchParams();
        const periodFrom = document.getElementById('from').value.trim();
        const periodTo = document.getElementById('to').value.trim();
        const topLimit = document.getElementById('topLimit').value.trim();
        if (periodFrom) params.set('period_from', periodFrom);
        if (periodTo) params.set('period_to', periodTo);
        if (topLimit) params.set('top_limit', topLimit);

        const response = await fetch('/ops/products/pricing-fiscal/overview?' + params.toString());
        const data = await response.json();
        document.getElementById('payload').textContent = JSON.stringify(data, null, 2);

        const comparison = data?.comparison || {};
        document.getElementById('kpiTotal').textContent = String(comparison.current ?? '-');
        document.getElementById('kpiDelta').textContent = data?.comparison ? `${comparison.delta_pct ?? 0}%` : '-';
        document.getElementById('kpiConfidence').textContent = data?.confidence_badge?.label || data?.confidence_level || '-';

        const defaultKpi = Array.isArray(data?.kpis) ? data.kpis.find((row) => row?.key === 'default_classifications') : null;
        document.getElementById('kpiDefault').textContent = String(defaultKpi?.current ?? '-');

        renderTopList('topPromotions', data?.tops_promotion_codes);
        renderTopList('topSkus', data?.tops_default_skus);
        renderTopList('topSource', data?.tops_fiscal_source);
      }
      loadData();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)

