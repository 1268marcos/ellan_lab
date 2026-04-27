from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.config import settings
from app.core.db import get_db
from app.jobs.integration_order_events_outbox import run_integration_order_events_outbox_once
from app.services.ops_audit_service import record_ops_action_audit
from app.schemas.integration_ops import (
    OrderEventOutboxDeadLetterPriorityItemOut,
    OrderEventOutboxDeadLetterPriorityOut,
    OrderEventOutboxPriorityReplayOut,
    OrderEventOutboxPriorityReplayRunItemOut,
    OrderEventOutboxPriorityReplayRunTimelineOut,
    OrderEventOutboxBatchReplayOut,
    OrderEventOutboxItemOut,
    OrderEventOutboxListOut,
    OrderEventOutboxReplayOut,
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
    if raw_value is not None and not isinstance(raw_value, str):
        raw_value = getattr(raw_value, "default", raw_value)
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


def _safe_rate_pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


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


@router.get("/order-events-outbox/dead-letter-priority", response_model=OrderEventOutboxDeadLetterPriorityOut)
def get_order_events_outbox_dead_letter_priority(
    partner_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from")
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    where_parts = ["status = 'DEAD_LETTER'"]
    params: dict[str, object] = {"limit": int(limit)}
    if str(partner_id or "").strip():
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = str(partner_id).strip()
    if str(event_type or "").strip():
        where_parts.append("event_type = :event_type")
        params["event_type"] = str(event_type).strip().upper()
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)

    summary_row = db.execute(
        text(
            f"""
            SELECT
                COUNT(*)::int AS total_dead_letters,
                COUNT(DISTINCT order_id)::int AS total_distinct_orders,
                COUNT(DISTINCT (partner_id, event_type))::int AS total_groups
            FROM partner_order_events_outbox
            WHERE {where_sql}
            """
        ),
        params,
    ).mappings().first()
    total_dead_letters = int((summary_row or {}).get("total_dead_letters") or 0)
    total_distinct_orders = int((summary_row or {}).get("total_distinct_orders") or 0)
    total_groups = int((summary_row or {}).get("total_groups") or 0)

    rows = db.execute(
        text(
            f"""
            SELECT
                partner_id,
                event_type,
                COUNT(*)::int AS dead_letter_count,
                COUNT(DISTINCT order_id)::int AS distinct_orders,
                MIN(created_at) AS oldest_created_at,
                MAX(created_at) AS newest_created_at,
                MAX(updated_at) AS latest_updated_at
            FROM partner_order_events_outbox
            WHERE {where_sql}
            GROUP BY partner_id, event_type
            ORDER BY dead_letter_count DESC, distinct_orders DESC, oldest_created_at ASC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    items = [
        OrderEventOutboxDeadLetterPriorityItemOut(
            partner_id=str(row.get("partner_id") or ""),
            event_type=str(row.get("event_type") or ""),
            dead_letter_count=int(row.get("dead_letter_count") or 0),
            distinct_orders=int(row.get("distinct_orders") or 0),
            oldest_created_at=_to_iso_utc(row.get("oldest_created_at")),
            newest_created_at=_to_iso_utc(row.get("newest_created_at")),
            latest_updated_at=_to_iso_utc(row.get("latest_updated_at")),
        )
        for row in rows
    ]
    return OrderEventOutboxDeadLetterPriorityOut(
        ok=True,
        total_groups=total_groups,
        total_dead_letters=total_dead_letters,
        total_distinct_orders=total_distinct_orders,
        limit=int(limit),
        items=items,
    )


@router.post("/order-events-outbox/replay-priority-groups", response_model=OrderEventOutboxPriorityReplayOut)
def replay_order_events_outbox_priority_groups(
    dry_run: bool = Query(default=True),
    run_after_replay: bool = Query(default=False),
    max_deliveries_after_replay: int | None = Query(default=None, ge=1, le=500),
    top_n_groups: int = Query(default=5, ge=1, le=100),
    max_items: int = Query(default=100, ge=1, le=500),
    partner_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    worker_run_limit_guard = 100
    if run_after_replay and dry_run:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_RUN_AFTER_REPLAY",
                "message": "run_after_replay=true exige dry_run=false.",
            },
        )
    if run_after_replay and int(max_items) > worker_run_limit_guard:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "RUN_AFTER_REPLAY_MAX_ITEMS_EXCEEDED",
                "message": "Quando run_after_replay=true, max_items deve ser <= 100.",
                "max_limit": worker_run_limit_guard,
            },
        )
    if max_deliveries_after_replay is not None and not run_after_replay:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_MAX_DELIVERIES_AFTER_REPLAY",
                "message": "max_deliveries_after_replay exige run_after_replay=true.",
            },
        )
    if max_deliveries_after_replay is not None and int(max_deliveries_after_replay) > worker_run_limit_guard:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "MAX_DELIVERIES_AFTER_REPLAY_LIMIT_EXCEEDED",
                "message": "max_deliveries_after_replay deve ser <= 100.",
                "max_limit": worker_run_limit_guard,
            },
        )

    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from")
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    where_parts = ["status = 'DEAD_LETTER'"]
    params: dict[str, object] = {"top_n_groups": int(top_n_groups)}
    normalized_partner_id = str(partner_id or "").strip()
    normalized_event_type = str(event_type or "").strip().upper()
    if normalized_partner_id:
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = normalized_partner_id
    if normalized_event_type:
        where_parts.append("event_type = :event_type")
        params["event_type"] = normalized_event_type
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    where_sql = " AND ".join(where_parts)

    priority_rows = db.execute(
        text(
            f"""
            SELECT
                partner_id,
                event_type,
                COUNT(*)::int AS dead_letter_count,
                COUNT(DISTINCT order_id)::int AS distinct_orders,
                MIN(created_at) AS oldest_created_at,
                MAX(created_at) AS newest_created_at,
                MAX(updated_at) AS latest_updated_at
            FROM partner_order_events_outbox
            WHERE {where_sql}
            GROUP BY partner_id, event_type
            ORDER BY dead_letter_count DESC, distinct_orders DESC, oldest_created_at ASC
            LIMIT :top_n_groups
            """
        ),
        params,
    ).mappings().all()
    groups = [
        OrderEventOutboxDeadLetterPriorityItemOut(
            partner_id=str(row.get("partner_id") or ""),
            event_type=str(row.get("event_type") or ""),
            dead_letter_count=int(row.get("dead_letter_count") or 0),
            distinct_orders=int(row.get("distinct_orders") or 0),
            oldest_created_at=_to_iso_utc(row.get("oldest_created_at")),
            newest_created_at=_to_iso_utc(row.get("newest_created_at")),
            latest_updated_at=_to_iso_utc(row.get("latest_updated_at")),
        )
        for row in priority_rows
    ]
    total_groups_selected = len(groups)

    outbox_rows: list[dict] = []
    total_candidates = 0
    if groups:
        group_clauses: list[str] = []
        select_params: dict[str, object] = {"max_items": int(max_items)}
        for idx, group in enumerate(groups):
            pk = f"g_partner_{idx}"
            ek = f"g_event_{idx}"
            group_clauses.append(f"(partner_id = :{pk} AND event_type = :{ek})")
            select_params[pk] = group.partner_id
            select_params[ek] = group.event_type
        grouped_where = " OR ".join(group_clauses)
        total_row = db.execute(
            text(
                f"""
                SELECT COUNT(*)::int AS total
                FROM partner_order_events_outbox
                WHERE status = 'DEAD_LETTER'
                  AND ({grouped_where})
                """
            ),
            select_params,
        ).mappings().first()
        total_candidates = int((total_row or {}).get("total") or 0)
        outbox_rows = db.execute(
            text(
                f"""
                SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
                FROM partner_order_events_outbox
                WHERE status = 'DEAD_LETTER'
                  AND ({grouped_where})
                ORDER BY created_at ASC, id ASC
                LIMIT :max_items
                """
            ),
            select_params,
        ).mappings().all()

    selected_count = len(outbox_rows)
    replayed_count = 0
    skipped_count = selected_count
    worker_run_payload: OrderEventOutboxRunOut | None = None
    execution_id = str(uuid4())
    selected_ids = [str(row.get("id") or "") for row in outbox_rows if str(row.get("id") or "").strip()]

    if not dry_run and selected_ids:
        db.execute(
            text(
                """
                UPDATE partner_order_events_outbox
                SET status = 'PENDING',
                    attempt_count = 0,
                    next_retry_at = NOW(),
                    last_error = NULL,
                    updated_at = NOW()
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": selected_ids},
        )
        replayed_count = len(selected_ids)
        skipped_count = selected_count - replayed_count
        record_ops_action_audit(
            db=db,
            action="I1_OUTBOX_MANUAL_REPLAY_PRIORITY_GROUPS",
            result="SUCCESS",
            correlation_id=f"corr-i1-replay-priority-{execution_id}",
            role="ops_user",
            details={
                "execution_id": execution_id,
                "dry_run": False,
                "top_n_groups": int(top_n_groups),
                "max_items": int(max_items),
                "total_groups_selected": total_groups_selected,
                "total_candidates": total_candidates,
                "selected_count": selected_count,
                "replayed_count": replayed_count,
                "sample_ids": selected_ids[:20],
            },
        )
        if run_after_replay and replayed_count > 0:
            worker_batch_size = int(max_deliveries_after_replay or min(int(max_items), worker_run_limit_guard))
            run_result = run_integration_order_events_outbox_once(
                db,
                batch_size=worker_batch_size,
                max_attempts=int(settings.integration_order_events_outbox_max_attempts),
                base_backoff_sec=int(settings.integration_order_events_outbox_base_backoff_sec),
            )
            worker_run_payload = OrderEventOutboxRunOut(ok=True, **run_result)

    db.execute(
        text(
            """
            INSERT INTO ops_outbox_replay_priority_runs (
                id, created_at, created_by_role, dry_run, run_after_replay,
                top_n_groups, max_items, total_groups_selected, total_candidates,
                selected_count, replayed_count, skipped_count, filters_json,
                selected_groups_json, worker_run_json
            ) VALUES (
                :id, NOW(), 'ops_user', :dry_run, :run_after_replay,
                :top_n_groups, :max_items, :total_groups_selected, :total_candidates,
                :selected_count, :replayed_count, :skipped_count, CAST(:filters_json AS JSONB),
                CAST(:selected_groups_json AS JSONB), CAST(:worker_run_json AS JSONB)
            )
            """
        ),
        {
            "id": execution_id,
            "dry_run": bool(dry_run),
            "run_after_replay": bool(run_after_replay),
            "top_n_groups": int(top_n_groups),
            "max_items": int(max_items),
            "total_groups_selected": total_groups_selected,
            "total_candidates": total_candidates,
            "selected_count": selected_count,
            "replayed_count": replayed_count,
            "skipped_count": skipped_count,
            "filters_json": json.dumps(
                {
                    "partner_id": normalized_partner_id or None,
                    "event_type": normalized_event_type or None,
                    "period_from": _to_iso_utc(dt_from) if dt_from else None,
                    "period_to": _to_iso_utc(dt_to) if dt_to else None,
                }
            ),
            "selected_groups_json": json.dumps([group.model_dump() for group in groups]),
            "worker_run_json": json.dumps(worker_run_payload.model_dump() if worker_run_payload else None),
        },
    )
    db.commit()

    final_rows = []
    if selected_ids:
        final_rows = db.execute(
            text(
                """
                SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
                FROM partner_order_events_outbox
                WHERE id = ANY(:ids)
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"ids": selected_ids},
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
        for row in final_rows
    ]

    return OrderEventOutboxPriorityReplayOut(
        ok=True,
        execution_id=execution_id,
        dry_run=bool(dry_run),
        run_after_replay=bool(run_after_replay),
        max_deliveries_after_replay=(
            int(max_deliveries_after_replay) if max_deliveries_after_replay is not None else None
        ),
        top_n_groups=int(top_n_groups),
        max_items=int(max_items),
        total_groups_selected=total_groups_selected,
        total_candidates=total_candidates,
        selected_count=selected_count,
        replayed_count=replayed_count,
        skipped_count=skipped_count,
        groups=groups,
        items=items,
        worker_run=worker_run_payload,
    )


@router.get(
    "/order-events-outbox/replay-priority-groups/runs",
    response_model=OrderEventOutboxPriorityReplayRunTimelineOut,
)
def get_order_events_outbox_priority_replay_runs_timeline(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    dry_run: bool | None = Query(default=None),
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
    if dt_from is not None:
        where_parts.append("created_at >= :dt_from")
        params["dt_from"] = dt_from
    if dt_to is not None:
        where_parts.append("created_at <= :dt_to")
        params["dt_to"] = dt_to
    if dry_run is not None:
        where_parts.append("dry_run = :dry_run")
        params["dry_run"] = bool(dry_run)
    where_sql = " AND ".join(where_parts)

    total_row = db.execute(
        text(f"SELECT COUNT(*)::int AS total FROM ops_outbox_replay_priority_runs WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT
                id, created_at, dry_run, run_after_replay,
                top_n_groups, max_items, total_groups_selected, total_candidates,
                selected_count, replayed_count, skipped_count
            FROM ops_outbox_replay_priority_runs
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    items = [
        OrderEventOutboxPriorityReplayRunItemOut(
            execution_id=str(row.get("id") or ""),
            created_at=_to_iso_utc(row.get("created_at")),
            dry_run=bool(row.get("dry_run")),
            run_after_replay=bool(row.get("run_after_replay")),
            top_n_groups=int(row.get("top_n_groups") or 0),
            max_items=int(row.get("max_items") or 0),
            total_groups_selected=int(row.get("total_groups_selected") or 0),
            total_candidates=int(row.get("total_candidates") or 0),
            selected_count=int(row.get("selected_count") or 0),
            replayed_count=int(row.get("replayed_count") or 0),
            skipped_count=int(row.get("skipped_count") or 0),
            effectiveness_rate_pct=_safe_rate_pct(
                int(row.get("replayed_count") or 0),
                int(row.get("selected_count") or 0),
            ),
        )
        for row in rows
    ]
    avg_effectiveness = _safe_rate_pct(
        sum(item.replayed_count for item in items),
        sum(item.selected_count for item in items),
    )
    return OrderEventOutboxPriorityReplayRunTimelineOut(
        ok=True,
        total=total,
        limit=int(limit),
        offset=int(offset),
        period_from=(_to_iso_utc(dt_from) if dt_from else None),
        period_to=(_to_iso_utc(dt_to) if dt_to else None),
        average_effectiveness_rate_pct=avg_effectiveness,
        items=items,
    )


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


@router.post("/order-events-outbox/{outbox_id}/replay", response_model=OrderEventOutboxReplayOut)
def replay_order_event_outbox_item(
    outbox_id: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE id = :id
            """
        ),
        {"id": outbox_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "OUTBOX_ITEM_NOT_FOUND", "message": "Item de outbox não encontrado."},
        )

    status = str(row.get("status") or "").upper()
    replayed = False
    reason: str | None = None
    if status in {"DELIVERED"} and not force:
        reason = "ITEM_ALREADY_DELIVERED_USE_FORCE"
    elif status in {"PENDING", "FAILED", "DEAD_LETTER", "SKIPPED"} or force:
        db.execute(
            text(
                """
                UPDATE partner_order_events_outbox
                SET status = 'PENDING',
                    attempt_count = 0,
                    next_retry_at = NOW(),
                    last_error = NULL,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": outbox_id},
        )
        replayed = True
        record_ops_action_audit(
            db=db,
            action="I1_OUTBOX_MANUAL_REPLAY",
            result="SUCCESS",
            correlation_id=f"corr-i1-replay-{outbox_id}",
            role="ops_user",
            order_id=str(row.get("order_id") or "") or None,
            details={
                "outbox_id": str(row.get("id") or ""),
                "partner_id": str(row.get("partner_id") or ""),
                "event_type": str(row.get("event_type") or ""),
                "previous_status": status,
                "force": bool(force),
            },
        )
        db.commit()
    else:
        reason = "ITEM_STATUS_NOT_REPLAYABLE"

    latest = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE id = :id
            """
        ),
        {"id": outbox_id},
    ).mappings().first()
    item = OrderEventOutboxItemOut(
        id=str(latest.get("id") or ""),
        partner_id=str(latest.get("partner_id") or ""),
        order_id=str(latest.get("order_id") or ""),
        event_type=str(latest.get("event_type") or ""),
        status=str(latest.get("status") or ""),
        attempt_count=int(latest.get("attempt_count") or 0),
        max_attempts=int(latest.get("max_attempts") or 0),
        next_retry_at=(_to_iso_utc(latest.get("next_retry_at")) if latest.get("next_retry_at") else None),
        delivered_at=(_to_iso_utc(latest.get("delivered_at")) if latest.get("delivered_at") else None),
        created_at=_to_iso_utc(latest.get("created_at")),
    )
    return OrderEventOutboxReplayOut(ok=True, replayed=replayed, reason=reason, item=item)


@router.post("/order-events-outbox/replay-batch", response_model=OrderEventOutboxBatchReplayOut)
def replay_order_events_outbox_batch(
    dry_run: bool = Query(default=True),
    run_after_replay: bool = Query(default=False),
    max_deliveries_after_replay: int | None = Query(default=None, ge=1, le=500),
    partner_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    worker_run_limit_guard = 100
    if run_after_replay and dry_run:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_RUN_AFTER_REPLAY",
                "message": "run_after_replay=true exige dry_run=false.",
            },
        )
    if run_after_replay and int(limit) > worker_run_limit_guard:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "RUN_AFTER_REPLAY_LIMIT_EXCEEDED",
                "message": "Quando run_after_replay=true, limit deve ser <= 100.",
                "max_limit": worker_run_limit_guard,
            },
        )
    if max_deliveries_after_replay is not None and not run_after_replay:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_MAX_DELIVERIES_AFTER_REPLAY",
                "message": "max_deliveries_after_replay exige run_after_replay=true.",
            },
        )
    if max_deliveries_after_replay is not None and int(max_deliveries_after_replay) > worker_run_limit_guard:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "MAX_DELIVERIES_AFTER_REPLAY_LIMIT_EXCEEDED",
                "message": "max_deliveries_after_replay deve ser <= 100.",
                "max_limit": worker_run_limit_guard,
            },
        )
    allowed_statuses = {"PENDING", "FAILED", "DEAD_LETTER", "SKIPPED"}
    normalized_status = str(status or "").strip().upper()
    if normalized_status and normalized_status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_REPLAY_STATUS_FILTER",
                "message": "status inválido para replay em lote.",
                "allowed_statuses": sorted(allowed_statuses),
            },
        )
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from")
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to")
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    where_parts = ["status IN ('PENDING','FAILED','DEAD_LETTER','SKIPPED')"]
    params: dict[str, object] = {"limit": int(limit)}
    if str(partner_id or "").strip():
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = str(partner_id).strip()
    if normalized_status:
        where_parts.append("status = :status")
        params["status"] = normalized_status
    if str(event_type or "").strip():
        where_parts.append("event_type = :event_type")
        params["event_type"] = str(event_type).strip().upper()
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
    total_candidates = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE {where_sql}
            ORDER BY created_at ASC, id ASC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    selected_count = len(rows)
    replayed_count = 0
    skipped_count = 0
    worker_run_payload: OrderEventOutboxRunOut | None = None

    if not dry_run and rows:
        ids = [str(row.get("id") or "") for row in rows if str(row.get("id") or "").strip()]
        if ids:
            db.execute(
                text(
                    """
                    UPDATE partner_order_events_outbox
                    SET status = 'PENDING',
                        attempt_count = 0,
                        next_retry_at = NOW(),
                        last_error = NULL,
                        updated_at = NOW()
                    WHERE id = ANY(:ids)
                    """
                ),
                {"ids": ids},
            )
            replayed_count = len(ids)
        skipped_count = selected_count - replayed_count
        record_ops_action_audit(
            db=db,
            action="I1_OUTBOX_MANUAL_REPLAY_BATCH",
            result="SUCCESS",
            correlation_id=f"corr-i1-replay-batch-{datetime.now(timezone.utc).timestamp()}",
            role="ops_user",
            details={
                "dry_run": False,
                "filters": {
                    "partner_id": str(partner_id or "") or None,
                    "status": normalized_status or None,
                    "event_type": (str(event_type).strip().upper() if str(event_type or "").strip() else None),
                    "period_from": _to_iso_utc(dt_from) if dt_from else None,
                    "period_to": _to_iso_utc(dt_to) if dt_to else None,
                },
                "selected_count": selected_count,
                "replayed_count": replayed_count,
                "sample_ids": ids[:20],
            },
        )
        db.commit()
        if run_after_replay and replayed_count > 0:
            worker_batch_size = int(max_deliveries_after_replay or min(int(limit), worker_run_limit_guard))
            run_result = run_integration_order_events_outbox_once(
                db,
                batch_size=worker_batch_size,
                max_attempts=int(settings.integration_order_events_outbox_max_attempts),
                base_backoff_sec=int(settings.integration_order_events_outbox_base_backoff_sec),
            )
            worker_run_payload = OrderEventOutboxRunOut(ok=True, **run_result)
    else:
        skipped_count = selected_count

    # recarrega os itens selecionados para refletir estado final (ou atual no dry_run)
    ids_for_read = [str(row.get("id") or "") for row in rows if str(row.get("id") or "").strip()]
    final_rows = []
    if ids_for_read:
        final_rows = db.execute(
            text(
                """
                SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
                FROM partner_order_events_outbox
                WHERE id = ANY(:ids)
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"ids": ids_for_read},
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
        for row in final_rows
    ]
    return OrderEventOutboxBatchReplayOut(
        ok=True,
        dry_run=bool(dry_run),
        run_after_replay=bool(run_after_replay),
        max_deliveries_after_replay=(int(max_deliveries_after_replay) if max_deliveries_after_replay is not None else None),
        total_candidates=total_candidates,
        selected_count=selected_count,
        replayed_count=replayed_count,
        skipped_count=skipped_count,
        limit=int(limit),
        items=items,
        worker_run=worker_run_payload,
    )


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
