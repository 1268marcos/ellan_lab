# 01_source/backend/order_lifecycle_service/app/services/deadline_engine.py
# 19/04/2026 - Refatoração: remoção de duplicação de verificação/status + fix de _normalize_db_text

from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.lifecycle import (
    AnalyticsFact,
    DeadlineStatus,
    DomainEvent,
    EventStatus,
    LifecycleDeadline,
)

from app.core.datetime_utils import to_iso_utc

#-------------------------------------
# HELPERS
#-------------------------------------
def utc_now():
    return datetime.now(timezone.utc)

def _mark_deadline_executed(deadline: LifecycleDeadline, now: datetime) -> bool:
    if deadline.status != DeadlineStatus.EXECUTING:
        return False
    deadline.status = DeadlineStatus.EXECUTED
    deadline.executed_at = now
    deadline.updated_at = now
    return True

def _normalize_db_text(value) -> str:
    """Garante retorno string uppercase e segura contra None."""
    if value is None:
        return ""
    return str(value).strip().upper()

def _order_is_already_paid_or_fulfilled(db: Session, order_id: str) -> bool:
    """
    Hardening defensivo:
    Consulta o estado real do pedido no banco central. Aborta a execução
    se o pagamento já foi confirmado ou se o pedido avançou para estágio pós-pagamento.
    """
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
    order_status     = _normalize_db_text(row.get("status"))
    paid_at          = row.get("paid_at")
    picked_up_at     = row.get("picked_up_at")

    # Verificação por timestamp (fonte da verdade mais confiável)
    if paid_at is not None or picked_up_at is not None:
        return True

    # Verificação por status textual
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

#-------------------------------------
# EXECUTORES
#-------------------------------------
def execute_prepayment_timeout(db: Session, deadline: LifecycleDeadline) -> None:
    now = utc_now()

    if deadline.status != DeadlineStatus.EXECUTING:
        return

    order_id = deadline.order_id
    order_channel = deadline.order_channel
    payload = deadline.payload or {}

    # 🔒 ÚNICA VERIFICAÇÃO DEFENSIVA (single source of truth)
    if _order_is_already_paid_or_fulfilled(db, order_id):
        deadline.status = DeadlineStatus.CANCELLED
        deadline.cancelled_at = now
        deadline.updated_at = now
        return

    # Se chegou aqui, o deadline pode ser executado com segurança
    deadline.status = DeadlineStatus.EXECUTED
    deadline.executed_at = now
    deadline.updated_at = now

    # 📤 Evento de Domínio
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

    # 📊 Fato Analítico
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
    now = utc_now()

    if not _mark_deadline_executed(deadline, now):
        return

    order_id = deadline.order_id
    order_channel = deadline.order_channel
    payload = deadline.payload or {}
    pickup_id = payload.get("pickup_id")

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
        region_code=payload.get("region_code"),
        slot_id=payload.get("slot_id"),
        payload={
            "order_id": order_id,
            "pickup_id": pickup_id,
            "terminal_state": "expired",
            "reason": "pickup_not_redeemed_before_deadline",
            "deadline_type": deadline.deadline_type.value,
            "due_at": to_iso_utc(deadline.due_at),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(fact)

    