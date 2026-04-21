# 01_source/order_pickup_service/app/jobs/lifecycle_events_consumer.py
# 18/04/2026 - melhorias para expiração de retirada no ONLINE (pagou e não foi retirar)
# 19/04/2026 - confirmação do event_name == "pickup.expired":

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.lifecycle_events_client import (
    LifecycleEventsClient,
    LifecycleEventsClientError,
)
from app.models.allocation import Allocation
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupStatus
from app.services import backend_client

from app.services.pickup_expiration_handler import handle_pickup_expired





logger = logging.getLogger(__name__)

LIFECYCLE_EVENTS_BATCH_SIZE = settings.lifecycle_events_batch_size


def run_lifecycle_events_consumer_once(db: Session) -> int:
    client = LifecycleEventsClient()

    try:
        response = client.list_pending_events(limit=LIFECYCLE_EVENTS_BATCH_SIZE)
    except LifecycleEventsClientError:
        logger.exception("lifecycle_events_list_failed")
        return 0

    items = response.get("items", []) or []
    if not items:
        return 0

    processed = 0

    for item in items:
        event_name = item.get("event_name")
        
        # if event_name != "order.prepayment_timed_out":
        #    continue

        event_key = item.get("event_key")
        payload = item.get("payload") or {}
        order_id = payload.get("order_id") or item.get("aggregate_id")

        if not event_key or not order_id:
            logger.warning(
                "lifecycle_event_missing_fields",
                extra={"event_key": event_key, "order_id": order_id},
            )
            continue

        try:
            # handled = _handle_prepayment_timeout(db=db, order_id=order_id, payload=payload)
            # if handled:
            #     client.ack_event(event_key=event_key)
            #     processed += 1
            handled = False

            if event_name == "order.prepayment_timed_out":
                handled = _handle_prepayment_timeout(
                    db=db,
                    order_id=order_id,
                    payload=payload
                )

            # BLOCO CRÍTICO
            elif event_name == "pickup.door_opened":
                handled = _handle_pickup_door_opened(
                    db=db,
                    order_id=order_id,
                    payload=payload
                )

            elif event_name in {
                "pickup.expired",
                "pickup.timed_out",
                "pickup.pickup_timed_out",
            }:
                handled = handle_pickup_expired(
                    db=db,
                    order_id=order_id,
                    payload=payload,
                )


            if handled:
                client.ack_event(event_key=event_key)
                processed += 1

        except LifecycleEventsClientError:
            logger.exception(
                "lifecycle_event_ack_failed",
                extra={"event_key": event_key, "order_id": order_id},
            )
            db.rollback()

        except Exception:
            logger.exception(
                "lifecycle_event_process_failed",
                extra={"event_key": event_key, "order_id": order_id},
            )
            db.rollback()

    if processed:
        logger.info("lifecycle_events_processed", extra={"processed": processed})

    return processed


def _handle_pickup_door_opened(
    *,
    db: Session,
    order_id: str,
    payload: dict[str, Any],
) -> bool:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning("pickup_door_opened_order_not_found", extra={"order_id": order_id})
        return True

    pickup = db.query(Pickup).filter(Pickup.order_id == order.id).first()

    # 🔥 estado final correto
    # OrderStatus.DISPENSED -> Máquina liberou - pickup.door_opened - NÃO tem como provar que cliente retirou fisicamente, só sabe que a porta abriu.
    order.status = OrderStatus.DISPENSED
    order.picked_up_at = payload.get("occurred_at")

    if pickup:
        pickup.status = PickupStatus.REDEEMED  # Retirada concluída - Antes errado com PickupStatus.COMPLETED

    db.commit()

    logger.info(
        "pickup_door_opened_applied",
        extra={
            "order_id": order.id,
        },
    )

    return True



def _resolve_locker_id(*, order: Order, allocation: Allocation | None) -> str | None:
    if allocation and getattr(allocation, "locker_id", None):
        return allocation.locker_id
    if getattr(order, "totem_id", None):
        return order.totem_id
    return None


def _handle_prepayment_timeout(*, db: Session, order_id: str, payload: dict[str, Any]) -> bool:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning("prepayment_timeout_order_not_found", extra={"order_id": order_id})
        return True

    if order.status != OrderStatus.PAYMENT_PENDING:
        logger.info(
            "prepayment_timeout_already_handled",
            extra={"order_id": order_id, "status": order.status.value},
        )
        return True

    # allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    # pickup = db.query(Pickup).filter(Pickup.order_id == order.id).first()
    # Pega a allocation mais recente (melhoria válida)
    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .order_by(Allocation.created_at.desc())
        .first()
    )

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc())
        .first()
    )

    region = payload.get("region_code") or order.region   # Mantém flexibilidade
    locker_id = _resolve_locker_id(order=order, allocation=allocation)

    # 🔥 Libera locker ANTES do commit (mantém da versão atual)
    if allocation and allocation.id:
        try:
            backend_client.locker_release(
                region,
                allocation.id,
                locker_id=locker_id,
            )

            if allocation.slot is not None:
                backend_client.locker_set_state(
                    region,
                    int(allocation.slot),
                    "AVAILABLE",
                    locker_id=locker_id,
                )
        except Exception:
            logger.exception(
                "prepayment_timeout_release_failed",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "slot": allocation.slot,
                    "region": region,
                    "locker_id": locker_id,
                },
            )
            raise  # 🔥 Mantém o raise para garantir consistência

    # Usa métodos de domínio (melhoria válida)
    order.status = OrderStatus.EXPIRED
    order.mark_payment_expired()


    # Se existir método mark_as_expired, use-o
    if hasattr(order, "mark_as_expired"):
        order.mark_as_expired(credit_50=False)


    if allocation:
        # allocation.mark_released()
        # Prefira mark_expired se existir, senão mark_released
        if hasattr(allocation, "mark_expired"):
            allocation.mark_expired()
        else:
            allocation.mark_released()


    if pickup and pickup.status == PickupStatus.ACTIVE:
        # pickup.status = PickupStatus.CANCELLED
        pickup.status = PickupStatus.EXPIRED  # Mantém EXPIRED (mais semântico)

    db.commit()

    logger.info(
        "prepayment_timeout_applied",
        extra={
            "order_id": order.id,
            "region": region,
            "locker_id": locker_id,
            "allocation_id": allocation.id if allocation else None,
            "slot": allocation.slot if allocation else None,
        },
    )
    return True



