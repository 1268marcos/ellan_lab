from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.config import settings
from app.core.db import get_db
from app.jobs.integration_order_events_outbox import run_integration_order_events_outbox_once
from app.schemas.integration_ops import (
    OrderEventOutboxItemOut,
    OrderEventOutboxListOut,
    OrderFulfillmentTrackingCompareOut,
    OrderFulfillmentTrackingItemOut,
    OrderFulfillmentTrackingListOut,
    OrderEventOutboxRunOut,
)

router = APIRouter(
    prefix="/ops/integration",
    tags=["integration-ops"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)


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


@router.get("/order-events-outbox", response_model=OrderEventOutboxListOut)
def get_order_events_outbox(
    status: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
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
    normalized_status = str(status or "").strip().upper()
    normalized_event = str(event_type or "").strip().upper()
    normalized_order = str(order_id or "").strip()
    if normalized_status:
        where_parts.append("status = :status")
        params["status"] = normalized_status
    if normalized_event:
        where_parts.append("event_type = :event_type")
        params["event_type"] = normalized_event
    if normalized_order:
        where_parts.append("order_id = :order_id")
        params["order_id"] = normalized_order
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)

    total_row = db.execute(
        text(f"SELECT COUNT(*) AS total FROM partner_order_events_outbox WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)

    rows = db.execute(
        text(
            f"""
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [
        OrderEventOutboxItemOut(
            id=str(row.get("id") or ""),
            partner_id=str(row.get("partner_id") or ""),
            order_id=str(row.get("order_id") or ""),
            event_type=str(row.get("event_type") or ""),
            status=str(row.get("status") or ""),
            attempt_count=int(row.get("attempt_count") or 0),
            max_attempts=int(row.get("max_attempts") or 0),
            next_retry_at=(_to_iso_utc(row.get("next_retry_at")) if row.get("next_retry_at") else None),
            delivered_at=(_to_iso_utc(row.get("delivered_at")) if row.get("delivered_at") else None),
            created_at=_to_iso_utc(row.get("created_at")),
        )
        for row in rows
    ]
    return OrderEventOutboxListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/order-events-outbox/run", response_model=OrderEventOutboxRunOut)
def run_order_events_outbox_now(
    batch_size: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
):
    result = run_integration_order_events_outbox_once(
        db,
        batch_size=int(batch_size or settings.integration_order_events_outbox_batch_size),
        max_attempts=int(settings.integration_order_events_outbox_max_attempts),
        base_backoff_sec=int(settings.integration_order_events_outbox_base_backoff_sec),
    )
    return OrderEventOutboxRunOut(ok=True, **result)


def _safe_delta_pct(current: int, previous: int) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100.0, 2)


@router.get("/order-fulfillment-tracking", response_model=OrderFulfillmentTrackingListOut)
def get_order_fulfillment_tracking(
    status: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
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
    if str(status or "").strip():
        where_parts.append("status = :status")
        params["status"] = str(status).strip().upper()
    if str(partner_id or "").strip():
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = str(partner_id).strip()
    if str(order_id or "").strip():
        where_parts.append("order_id = :order_id")
        params["order_id"] = str(order_id).strip()
    if dt_from is not None:
        where_parts.append("updated_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("updated_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)
    total_row = db.execute(
        text(f"SELECT COUNT(*) AS total FROM order_fulfillment_tracking WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT id, order_id, fulfillment_type, partner_id, status, last_event_type, last_outbox_status, updated_at
            FROM order_fulfillment_tracking
            WHERE {where_sql}
            ORDER BY updated_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [
        OrderFulfillmentTrackingItemOut(
            id=str(row.get("id") or ""),
            order_id=str(row.get("order_id") or ""),
            fulfillment_type=str(row.get("fulfillment_type") or ""),
            partner_id=(str(row.get("partner_id")) if row.get("partner_id") is not None else None),
            status=str(row.get("status") or ""),
            last_event_type=(str(row.get("last_event_type")) if row.get("last_event_type") is not None else None),
            last_outbox_status=(str(row.get("last_outbox_status")) if row.get("last_outbox_status") is not None else None),
            updated_at=_to_iso_utc(row.get("updated_at")),
        )
        for row in rows
    ]
    return OrderFulfillmentTrackingListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.get("/order-fulfillment-tracking/compare", response_model=OrderFulfillmentTrackingCompareOut)
def compare_order_fulfillment_tracking(
    period_from: str = Query(...),
    period_to: str = Query(...),
    partner_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from")
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to")
    if dt_from is None or dt_to is None:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "period_from e period_to são obrigatórios."})
    if dt_from > dt_to:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."})
    window = dt_to - dt_from
    previous_to = dt_from
    previous_from = dt_from - window
    where_partner = ""
    params: dict[str, object] = {
        "dt_from": dt_from,
        "dt_to": dt_to,
        "prev_from": previous_from,
        "prev_to": previous_to,
    }
    if str(partner_id or "").strip():
        where_partner = " AND partner_id = :partner_id"
        params["partner_id"] = str(partner_id).strip()
    current_rows = db.execute(
        text(
            f"""
            SELECT status, COUNT(*)::int AS count
            FROM order_fulfillment_tracking
            WHERE updated_at >= :dt_from AND updated_at <= :dt_to {where_partner}
            GROUP BY status
            """
        ),
        params,
    ).mappings().all()
    previous_rows = db.execute(
        text(
            f"""
            SELECT status, COUNT(*)::int AS count
            FROM order_fulfillment_tracking
            WHERE updated_at >= :prev_from AND updated_at <= :prev_to {where_partner}
            GROUP BY status
            """
        ),
        params,
    ).mappings().all()
    current_by_status = {str(r.get("status") or ""): int(r.get("count") or 0) for r in current_rows}
    previous_by_status = {str(r.get("status") or ""): int(r.get("count") or 0) for r in previous_rows}
    current_total = sum(current_by_status.values())
    previous_total = sum(previous_by_status.values())
    return OrderFulfillmentTrackingCompareOut(
        ok=True,
        period_from=_to_iso_utc(dt_from),
        period_to=_to_iso_utc(dt_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        current_total=current_total,
        previous_total=previous_total,
        delta_pct=_safe_delta_pct(current_total, previous_total),
        current_by_status=current_by_status,
        previous_by_status=previous_by_status,
    )
