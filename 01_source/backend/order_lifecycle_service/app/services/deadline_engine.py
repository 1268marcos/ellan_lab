# 01_source/backend/order_lifecycle_service/app/services/deadline_engine.py
# 18/04/2026 - criado hardening adicional para executar def execute_prepayment_timeout()
# 18/04/2026 - HARDENING: Adicionada validação defensiva para verificar se o pedido já foi pago

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


#-------------------------------------
# HELPERS
#-------------------------------------
def utc_now():
    return datetime.now(timezone.utc)


def _order_is_already_paid_or_fulfilled(db: Session, order_id: str) -> bool:
    """
    Hardening defensivo:
    antes de executar PREPAYMENT_TIMEOUT, consulta o estado real do pedido
    no banco central e aborta a execução se o pagamento já foi confirmado
    ou se o pedido já avançou para estágio pós-pagamento.
    """
    row = db.execute(
        text(
            """
            SELECT
                payment_status,
                status,
                paid_at,
                picked_up_at
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

    if paid_at is not None:
        return True

    if picked_up_at is not None:
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



def execute_prepayment_timeout(db: Session, deadline: LifecycleDeadline) -> None:
    now = utc_now()

    if deadline.status != DeadlineStatus.EXECUTING:
        return

    order_id = deadline.order_id
    order_channel = deadline.order_channel
    payload = deadline.payload or {}

    # 🔥 HARDENING DEFENSIVO
    # Se o pedido já foi pago/confirmado, este timeout não deve gerar
    # evento de abandono nem analytics de payment timeout.
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
            "due_at": deadline.due_at.isoformat(),
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
            "due_at": deadline.due_at.isoformat(),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(fact)

    