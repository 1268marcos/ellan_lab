# 01_source/backend/order_lifecycle_service/app/services/deadline_engine.py
# 21/04/2026 - PRODUÇÃO
# - PREPAYMENT_TIMEOUT sem duplicação
# - PICKUP_TIMEOUT com efeito operacional real
# - runtime release no mesmo fluxo
# - idempotente
# - crédito 50% com validade de 30 dias
# - mantém DomainEvent + AnalyticsFact
# - observabilidade

from __future__ import annotations

import logging

from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.lifecycle import (
    AnalyticsFact,
    DeadlineStatus,
    DomainEvent,
    EventStatus,
    LifecycleDeadline,
)
from app.clients.runtime_client import RuntimeClient, RuntimeClientError
from app.core.datetime_utils import to_iso_utc


logger = logging.getLogger(__name__)



def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_iso(dt):
    if dt is None:
        return None
    return to_iso_utc(dt)

def _log_pickup_timeout_step(logger, *, step: str, order_id: str, extra: dict | None = None):
    payload = {
        "pickup_timeout_step": step,
        "order_id": order_id,
    }
    if extra:
        payload.update(extra)
    logger.info("pickup_timeout_step", extra=payload)

def _log_pickup_timeout_error(logger, *, step: str, order_id: str, error: Exception, extra: dict | None = None):
    payload = {
        "pickup_timeout_step": step,
        "order_id": order_id,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
    }
    if extra:
        payload.update(extra)
    logger.exception("pickup_timeout_step_failed", extra=payload)





def _mark_deadline_executed(deadline: LifecycleDeadline, now: datetime) -> bool:
    if deadline.status != DeadlineStatus.EXECUTING:
        return False
    deadline.status = DeadlineStatus.EXECUTED
    deadline.executed_at = now
    deadline.updated_at = now
    return True


def _normalize_db_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _order_is_already_paid_or_fulfilled(db: Session, order_id: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT payment_status, status, paid_at, picked_up_at
            FROM public.orders
            WHERE id = :order_id
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()

    if not row:
        return False

    payment_status = _normalize_db_text(row.get("payment_status"))
    order_status = _normalize_db_text(row.get("status"))
    paid_at = row.get("paid_at")
    picked_up_at = row.get("picked_up_at")

    if paid_at is not None or picked_up_at is not None:
        return True

    if payment_status in {"APPROVED", "PAID", "CAPTURED", "SETTLED"}:
        return True

    if order_status in {
        "PAID_PENDING_PICKUP",
        "DISPENSED",
        "PICKED_UP",
        "COMPLETED",
        "FULFILLED",
    }:
        return True

    return False


def _is_order_terminal_for_pickup_timeout(order_status: str) -> bool:
    return order_status in {
        "EXPIRED",
        "EXPIRED_CREDIT_50",
        "PICKED_UP",
        "DISPENSED",
        "CANCELLED",
        "REFUNDED",
        "FAILED",
    }


def _get_order_snapshot(db: Session, order_id: str) -> dict | None:
    return db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                amount_cents,
                region,
                totem_id,
                status,
                payment_status,
                channel,
                pickup_deadline_at,
                paid_at,
                picked_up_at
            FROM public.orders
            WHERE id = :order_id
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()


def _get_latest_pickup(db: Session, order_id: str) -> dict | None:
    return db.execute(
        text(
            """
            SELECT
                id,
                status,
                lifecycle_stage,
                expires_at,
                locker_id,
                machine_id,
                slot
            FROM public.pickups
            WHERE order_id = :order_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()


def _get_latest_allocation(db: Session, order_id: str) -> dict | None:
    return db.execute(
        text(
            """
            SELECT
                id,
                locker_id,
                slot,
                state,
                locked_until,
                released_at
            FROM public.allocations
            WHERE order_id = :order_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()


def _invalidate_active_pickup_tokens(db: Session, pickup_id: str, now: datetime) -> int:
    result = db.execute(
        text(
            """
            UPDATE public.pickup_tokens
            SET used_at = :now
            WHERE pickup_id = :pickup_id
              AND used_at IS NULL
            """
        ),
        {
            "pickup_id": pickup_id,
            "now": now.replace(tzinfo=None),
        },
    )
    return int(result.rowcount or 0)
"""
Alembic migration: add unique constraint (index) on credits (order_id, source_type='PICKUP_EXPIRATION')
Revision ID: add_unique_constraint_credits_order_source
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_unique_constraint_credits_order_source'
down_revision = None  # Atualize conforme necessário (set to last/current revision id)
branch_labels = None
depends_on = None

INDEX_NAME = "ux_credits_order_source"

def upgrade() -> None:
    # Cria o índice único de forma concorrente para (order_id, source_type) onde source_type='PICKUP_EXPIRATION'
    op.execute(
        f"""
        CREATE UNIQUE INDEX CONCURRENTLY {INDEX_NAME}
          ON public.credits (order_id, source_type)
          WHERE source_type = 'PICKUP_EXPIRATION';
        """
    )

def downgrade() -> None:
    # Remove o índice criado acima de forma concorrente
    op.execute(
        f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX_NAME};"
    )


def _fetch_pickup_expiration_credit(db: Session, order_id: str) -> dict | None:
    return db.execute(
        text(
            """
            SELECT id, amount_cents, status, expires_at
            FROM public.credits
            WHERE order_id = :order_id
              AND source_type = 'PICKUP_EXPIRATION'
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()


def _ensure_credit_50(db: Session, *, order_row: dict, now: datetime) -> dict:
    user_id = order_row.get("user_id")
    amount_cents = int(order_row.get("amount_cents") or 0)

    if not user_id or amount_cents <= 0:
        return {
            "created": False,
            "exists": False,
            "credit_id": None,
            "amount_cents": 0,
            "status": None,
            "expires_at": None,
            "reason": "missing_user_or_amount",
        }

    credit_amount_cents = max(int(round(amount_cents * 0.5)), 0)
    if credit_amount_cents <= 0:
        return {
            "created": False,
            "exists": False,
            "credit_id": None,
            "amount_cents": 0,
            "status": None,
            "expires_at": None,
            "reason": "invalid_credit_amount",
        }

    order_id = order_row["id"]
    credit_id = str(uuid4())
    expires_at = now + timedelta(days=30)
    source_type = "PICKUP_EXPIRATION"

    insert_result = db.execute(
        text(
            """
            INSERT INTO public.credits (
                id,
                user_id,
                order_id,
                amount_cents,
                status,
                created_at,
                updated_at,
                expires_at,
                used_at,
                revoked_at,
                source_type,
                source_reason,
                notes
            ) VALUES (
                :id,
                :user_id,
                :order_id,
                :amount_cents,
                'AVAILABLE',
                :created_at,
                :updated_at,
                :expires_at,
                NULL,
                NULL,
                :source_type,
                :source_reason,
                :notes
            )
            ON CONFLICT (order_id, source_type)
            WHERE source_type = 'PICKUP_EXPIRATION'
            DO NOTHING
            """
        ),
        {
            "id": credit_id,
            "user_id": user_id,
            "order_id": order_id,
            "amount_cents": credit_amount_cents,
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at,
            "source_type": source_type,
            "source_reason": "pickup_not_redeemed_before_deadline",
            "notes": "Crédito automático de 50% por expiração de retirada.",
        },
    )

    if int(insert_result.rowcount or 0) == 1:
        return {
            "created": True,
            "exists": False,
            "credit_id": credit_id,
            "amount_cents": credit_amount_cents,
            "status": "AVAILABLE",
            "expires_at": expires_at,
            "reason": "created",
        }

    existing = _fetch_pickup_expiration_credit(db, order_id)
    if existing:
        return {
            "created": False,
            "exists": True,
            "credit_id": existing["id"],
            "amount_cents": int(existing["amount_cents"] or 0),
            "status": existing["status"],
            "expires_at": existing["expires_at"],
            "reason": "already_exists",
        }

    return {
        "created": False,
        "exists": False,
        "credit_id": None,
        "amount_cents": 0,
        "status": None,
        "expires_at": None,
        "reason": "insert_conflict_unresolved",
    }


def _apply_runtime_release_legacy_sem_observabilidade(
    *,
    region_code: str | None,
    locker_id: str | None,
    slot: int | None,
    allocation_id: str | None,
) -> dict:
    runtime = RuntimeClient()

    result = {
        "runtime_release_attempted": False,
        "runtime_set_state_attempted": False,
        "runtime_release_ok": False,
        "runtime_set_state_ok": False,
        "runtime_error": None,
    }

    if not region_code:
        result["runtime_error"] = "missing_region_code"
        return result

    try:
        if slot is not None:
            result["runtime_set_state_attempted"] = True
            runtime.locker_set_state(
                region=region_code,
                slot=int(slot),
                state="AVAILABLE",
                locker_id=locker_id,
            )
            result["runtime_set_state_ok"] = True

        if allocation_id:
            result["runtime_release_attempted"] = True
            runtime.locker_release(
                region=region_code,
                allocation_id=allocation_id,
                locker_id=locker_id,
            )
            result["runtime_release_ok"] = True

        return result

    except RuntimeClientError as exc:
        result["runtime_error"] = str(exc)
        raise


def _apply_runtime_release(
    *,
    region_code: str | None,
    locker_id: str | None,
    slot: int | None,
    allocation_id: str | None,
) -> dict:
    """
    Compensação saga: libera allocation no runtime antes de marcar slot AVAILABLE.
    Se o release falhar, o slot não é alterado (estado local já commitado permanece
    consistente com allocation ainda reservada no runtime até retry).
    """
    runtime = RuntimeClient()

    result = {
        "runtime_release_attempted": False,
        "runtime_set_state_attempted": False,
        "runtime_release_ok": False,
        "runtime_set_state_ok": False,
        "runtime_error": None,
    }

    log_order_id = allocation_id or "unknown"
    runtime_ctx = {
        "region_code": region_code,
        "locker_id": locker_id,
        "slot": int(slot) if slot is not None else None,
        "allocation_id": allocation_id,
    }

    if not region_code:
        result["runtime_error"] = "missing_region_code"
        return result

    def _log_runtime_failure(*, step: str, exc: RuntimeClientError) -> None:
        result["runtime_error"] = str(exc)
        _log_pickup_timeout_error(
            logger,
            step=step,
            order_id=log_order_id,
            error=exc,
            extra={**runtime_ctx, **result},
        )

    try:
        if allocation_id:
            result["runtime_release_attempted"] = True
            _log_pickup_timeout_step(
                logger,
                step="runtime_release_start",
                order_id=log_order_id,
                extra=runtime_ctx,
            )

            release_response = runtime.locker_release(
                region=region_code,
                allocation_id=allocation_id,
                locker_id=locker_id,
            )

            result["runtime_release_ok"] = True
            _log_pickup_timeout_step(
                logger,
                step="runtime_release_ok",
                order_id=log_order_id,
                extra={**runtime_ctx, "runtime_response": release_response},
            )

        if slot is not None:
            result["runtime_set_state_attempted"] = True
            _log_pickup_timeout_step(
                logger,
                step="runtime_set_state_start",
                order_id=log_order_id,
                extra={**runtime_ctx, "target_state": "AVAILABLE"},
            )

            set_state_response = runtime.locker_set_state(
                region=region_code,
                slot=int(slot),
                state="AVAILABLE",
                locker_id=locker_id,
            )

            result["runtime_set_state_ok"] = True
            _log_pickup_timeout_step(
                logger,
                step="runtime_set_state_ok",
                order_id=log_order_id,
                extra={**runtime_ctx, "runtime_response": set_state_response},
            )

        return result

    except RuntimeClientError as exc:
        if result["runtime_release_attempted"] and not result["runtime_release_ok"]:
            _log_runtime_failure(step="runtime_release_failed", exc=exc)
        elif result["runtime_set_state_attempted"] and not result["runtime_set_state_ok"]:
            _log_runtime_failure(step="runtime_set_state_failed", exc=exc)
        else:
            _log_runtime_failure(step="runtime_release_failed", exc=exc)
        raise



def _apply_pickup_timeout_state(db: Session, *, deadline: LifecycleDeadline, now: datetime) -> dict:
    order_id = deadline.order_id

    order_row = _get_order_snapshot(db, order_id)
    if not order_row:
        return {
            "applied": False,
            "reason": "order_not_found",
            "order_id": order_id,
        }

    order_status = _normalize_db_text(order_row.get("status"))
    if _is_order_terminal_for_pickup_timeout(order_status):
        return {
            "applied": False,
            "reason": "order_already_terminal",
            "order_id": order_id,
            "order_status": order_status,
        }

    pickup_row = _get_latest_pickup(db, order_id)
    allocation_row = _get_latest_allocation(db, order_id)

    invalidated_tokens = 0
    pickup_id = None
    slot = None
    locker_id = None
    allocation_id = None

    if pickup_row:
        pickup_id = pickup_row["id"]
        slot = pickup_row.get("slot")
        locker_id = pickup_row.get("locker_id") or pickup_row.get("machine_id")

        db.execute(
            text(
                """
                UPDATE public.pickups
                SET
                    status = 'EXPIRED',
                    lifecycle_stage = 'EXPIRED',
                    expired_at = :now,
                    expires_at = COALESCE(expires_at, :deadline_due_at)
                WHERE id = :pickup_id
                """
            ),
            {
                "pickup_id": pickup_id,
                "now": now,
                "deadline_due_at": deadline.due_at,
            },
        )

        invalidated_tokens = _invalidate_active_pickup_tokens(db, pickup_id, now)

    if allocation_row:
        allocation_id = allocation_row["id"]
        slot = allocation_row.get("slot")
        locker_id = locker_id or allocation_row.get("locker_id")

        db.execute(
            text(
                """
                UPDATE public.allocations
                SET
                    state = 'RELEASED',
                    released_at = COALESCE(released_at, :now),
                    locked_until = NULL
                WHERE id = :allocation_id
                """
            ),
            {
                "allocation_id": allocation_id,
                "now": now,
            },
        )

    credit_result = _ensure_credit_50(db, order_row=order_row, now=now)
    final_order_status = (
        "EXPIRED_CREDIT_50"
        if credit_result["created"] or credit_result["exists"]
        else "EXPIRED"
    )

    db.execute(
        text(
            """
            UPDATE public.orders
            SET
                status = CAST(:status AS public.orderstatus),
                updated_at = :now
            WHERE id = :order_id
            """
        ),
        {
            "order_id": order_id,
            "status": final_order_status,
            "now": now,
        },
    )

    runtime_result = _apply_runtime_release(
        region_code=order_row.get("region"),
        locker_id=locker_id or order_row.get("totem_id"),
        slot=int(slot) if slot is not None else None,
        allocation_id=allocation_id,
    )

    return {
        "applied": True,
        "reason": "ok",
        "order_id": order_id,
        "order_status": final_order_status,
        "pickup_id": pickup_id,
        "allocation_id": allocation_id,
        "slot": slot,
        "locker_id": locker_id or order_row.get("totem_id"),
        "region_code": order_row.get("region"),
        "invalidated_tokens": invalidated_tokens,
        "credit_created": credit_result["created"],
        "credit_exists": credit_result["exists"],
        "credit_id": credit_result["credit_id"],
        "credit_amount_cents": credit_result["amount_cents"],
        "credit_status": credit_result["status"],
        "credit_expires_at": (
            to_iso_utc(credit_result["expires_at"])
            if credit_result["expires_at"] is not None
            else None
        ),
        "channel": order_row.get("channel"),
        **runtime_result,
    }


def execute_prepayment_timeout(db: Session, deadline: LifecycleDeadline) -> None:
    now = _utc_now()

    if deadline.status != DeadlineStatus.EXECUTING:
        return

    order_id = deadline.order_id
    order_channel = deadline.order_channel
    payload = deadline.payload or {}

    if _order_is_already_paid_or_fulfilled(db, order_id):
        deadline.status = DeadlineStatus.CANCELLED
        deadline.cancelled_at = now
        deadline.updated_at = now
        return

    deadline.status = DeadlineStatus.EXECUTED
    deadline.executed_at = now
    deadline.updated_at = now

    event = DomainEvent(
        event_key=f"order.prepayment_timed_out:{order_id}",
        aggregate_type="order",
        aggregate_id=order_id,
        event_name="order.prepayment_timed_out",
        event_version=1,
        status=EventStatus.PENDING,
        payload={
            "order_id": order_id,
            "order_channel": order_channel,
            "deadline_type": deadline.deadline_type.value,
            "due_at": to_iso_utc(deadline.due_at),
            "reason": "payment_not_confirmed_before_deadline",
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(event)

    fact = AnalyticsFact(
        fact_key=f"order_abandoned_before_payment:{order_id}",
        fact_name="order_abandoned_before_payment",
        order_id=order_id,
        order_channel=order_channel,
        region_code=payload.get("region_code"),
        slot_id=payload.get("slot_id"),
        payload={
            "order_id": order_id,
            "abandonment_stage": "prepayment",
            "reason": "payment_not_confirmed_before_deadline",
            "deadline_type": deadline.deadline_type.value,
            "due_at": to_iso_utc(deadline.due_at),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(fact)


def execute_pickup_timeout(db: Session, deadline: LifecycleDeadline) -> None:
    now = _utc_now()

    if not _mark_deadline_executed(deadline, now):
        return

    payload = deadline.payload or {}
    order_id = deadline.order_id
    order_channel = deadline.order_channel

    result = _apply_pickup_timeout_state(
        db,
        deadline=deadline,
        now=now,
    )



    _log_pickup_timeout_step(
        logger,
        step="pickup_timeout_applied",
        order_id=order_id,
        extra={
            "pickup_id": result.get("pickup_id"),
            "allocation_id": result.get("allocation_id"),
            "slot": result.get("slot"),
            "locker_id": result.get("locker_id"),
            "region_code": result.get("region_code"),
            "order_status": result.get("order_status"),
            "invalidated_tokens": result.get("invalidated_tokens", 0),
            "credit_created": result.get("credit_created", False),
            "credit_id": result.get("credit_id"),
            "credit_amount_cents": result.get("credit_amount_cents", 0),
            "credit_expires_at": result.get("credit_expires_at"),
            "runtime_release_attempted": result.get("runtime_release_attempted", False),
            "runtime_set_state_attempted": result.get("runtime_set_state_attempted", False),
            "runtime_release_ok": result.get("runtime_release_ok", False),
            "runtime_set_state_ok": result.get("runtime_set_state_ok", False),
            "runtime_error": result.get("runtime_error"),
            "deadline_due_at": _safe_iso(deadline.due_at),
        },
    )




    pickup_id = result.get("pickup_id") or payload.get("pickup_id")
    region_code = result.get("region_code") or payload.get("region_code")
    slot_id = (
        str(result.get("slot"))
        if result.get("slot") is not None
        else payload.get("slot_id")
    )

    event = DomainEvent(
        event_key=f"pickup.expired:{pickup_id or order_id}",
        aggregate_type="pickup",
        aggregate_id=pickup_id or order_id,
        event_name="pickup.expired",
        event_version=1,
        status=EventStatus.PENDING,
        payload={
            "order_id": order_id,
            "pickup_id": pickup_id,
            "order_channel": order_channel,
            "deadline_type": deadline.deadline_type.value,
            "due_at": to_iso_utc(deadline.due_at),
            "reason": "pickup_not_redeemed_before_deadline",
            "applied": result.get("applied", False),
            "apply_reason": result.get("reason"),
            "order_status": result.get("order_status"),
            "allocation_id": result.get("allocation_id"),
            "slot": result.get("slot"),
            "locker_id": result.get("locker_id"),
            "invalidated_tokens": result.get("invalidated_tokens", 0),
            "credit_created": result.get("credit_created", False),
            "credit_exists": result.get("credit_exists", False),
            "credit_id": result.get("credit_id"),
            "credit_amount_cents": result.get("credit_amount_cents", 0),
            "credit_status": result.get("credit_status"),
            "credit_expires_at": result.get("credit_expires_at"),
            "runtime_release_attempted": result.get("runtime_release_attempted", False),
            "runtime_set_state_attempted": result.get("runtime_set_state_attempted", False),
            "runtime_release_ok": result.get("runtime_release_ok", False),
            "runtime_set_state_ok": result.get("runtime_set_state_ok", False),
            "runtime_error": result.get("runtime_error"),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(event)

    fact = AnalyticsFact(
        fact_key=f"pickup_expired:{pickup_id or order_id}",
        fact_name="pickup_expired",
        order_id=order_id,
        order_channel=order_channel,
        region_code=region_code,
        slot_id=slot_id,
        payload={
            "order_id": order_id,
            "pickup_id": pickup_id,
            "terminal_state": "expired",
            "reason": "pickup_not_redeemed_before_deadline",
            "deadline_type": deadline.deadline_type.value,
            "due_at": to_iso_utc(deadline.due_at),
            "applied": result.get("applied", False),
            "apply_reason": result.get("reason"),
            "order_status": result.get("order_status"),
            "allocation_id": result.get("allocation_id"),
            "slot": result.get("slot"),
            "locker_id": result.get("locker_id"),
            "invalidated_tokens": result.get("invalidated_tokens", 0),
            "credit_created": result.get("credit_created", False),
            "credit_exists": result.get("credit_exists", False),
            "credit_id": result.get("credit_id"),
            "credit_amount_cents": result.get("credit_amount_cents", 0),
            "credit_status": result.get("credit_status"),
            "credit_expires_at": result.get("credit_expires_at"),
            "runtime_release_attempted": result.get("runtime_release_attempted", False),
            "runtime_set_state_attempted": result.get("runtime_set_state_attempted", False),
            "runtime_release_ok": result.get("runtime_release_ok", False),
            "runtime_set_state_ok": result.get("runtime_set_state_ok", False),
            "runtime_error": result.get("runtime_error"),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(fact)


    