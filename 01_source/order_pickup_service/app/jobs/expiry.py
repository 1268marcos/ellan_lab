# 01_source/order_pickup_service/app/jobs/expiry.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import Pickup, PickupStatus
from app.services import backend_client
from app.services.credits_service import restore_credit_after_failed_order_creation

logger = logging.getLogger(__name__)

BATCH_SIZE = settings.expiry_batch_size
MAX_RETRIES = settings.expiry_max_retries

ENABLE_CREDIT = settings.expiry_enable_credit
CREDIT_RATIO = settings.expiry_credit_ratio


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt

    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _try_import_credit():
    try:
        from app.models.credit import Credit, CreditStatus  # type: ignore
        return Credit, CreditStatus
    except Exception:
        return None, None


def _resolve_locker_id(*, order: Order, allocation: Allocation | None) -> str | None:
    if allocation and getattr(allocation, "locker_id", None):
        return allocation.locker_id
    if getattr(order, "totem_id", None):
        return order.totem_id
    return None


def run_expiry_once(db: Session) -> int:
    """
    Expira pedidos ONLINE que passaram do pickup_deadline_at:
      - Order: PAID_PENDING_PICKUP -> EXPIRED
      - Pickup: ACTIVE -> EXPIRED
      - Allocation: RESERVED_PAID_PENDING_PICKUP -> EXPIRED
      - Slot no backend: OUT_OF_STOCK (cinza, aguardando reposição)
      - Backend allocation: locker_release(allocation_id) (best-effort)
      - Crédito 50% (opcional)
    """
    now = _as_naive_utc(_utc_now())
    changed = 0

    expired_orders = (
        db.query(Order)
        .filter(
            Order.channel == OrderChannel.ONLINE,
            Order.status == OrderStatus.PAID_PENDING_PICKUP,
            Order.pickup_deadline_at.isnot(None),
            Order.pickup_deadline_at <= now,
        )
        .limit(BATCH_SIZE)
        .all()
    )

    if not expired_orders:
        return 0

    logger.info(
        f"[expiry] encontrados {len(expired_orders)} pedidos expirados (batch={BATCH_SIZE})"
    )

    processed: list[dict] = []

    for order in expired_orders:
        try:
            result = _process_one(db, order)
            if result:
                processed.append(result)
                changed += 1
                db.commit()
            else:
                db.rollback()
        except Exception as e:
            db.rollback()
            logger.error(f"[expiry] erro ao processar order={order.id}: {e}", exc_info=True)

    for item in processed:
        try:
            _external_effects(
                order_id=item["order_id"],
                allocation_id=item["allocation_id"],
                slot=item["slot"],
                region=item["region"],
                locker_id=item["locker_id"],
            )
        except Exception as e:
            logger.error(
                f"[expiry] erro efeitos externos order={item['order_id']}: {e}",
                exc_info=True,
            )

    logger.info(f"[expiry] batch finalizado: {changed}/{len(expired_orders)}")
    return changed


def _process_one(db: Session, order: Order) -> Optional[dict]:
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        return None

    region = getattr(order, "region", None) or "PT"

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .first()
    )

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .first()
    )

    locker_id = _resolve_locker_id(order=order, allocation=allocation)

    credit_restored = restore_credit_after_failed_order_creation(
        db=db,
        order_metadata=getattr(order, "order_metadata", None),
    )
    if credit_restored:
        logger.info("[expiry] crédito de checkout reaberto order=%s", order.id)

    if ENABLE_CREDIT:
        Credit, CreditStatus = _try_import_credit()
        if Credit and CreditStatus and getattr(order, "user_id", None) and getattr(order, "amount_cents", None):
            try:
                existing = db.query(Credit).filter(Credit.order_id == order.id).first()
                if not existing:
                    credit_amount = int(int(order.amount_cents) * CREDIT_RATIO)
                    credit = Credit(
                        id=Credit.new_id(),
                        user_id=order.user_id,
                        order_id=order.id,
                        amount_cents=credit_amount,
                        status=CreditStatus.AVAILABLE,
                    )
                    db.add(credit)
                    logger.info(f"[expiry] crédito {credit_amount} cents criado order={order.id}")
            except Exception as e:
                logger.warning(f"[expiry] falha ao criar crédito order={order.id}: {e}")

    order.status = OrderStatus.EXPIRED
    order.mark_payment_expired()

    pickup_id = None
    if pickup:
        pickup_id = pickup.id

        if pickup.status == PickupStatus.ACTIVE:
            pickup.status = PickupStatus.EXPIRED

        if order.pickup_deadline_at:
            pickup.expires_at = order.pickup_deadline_at

    alloc_id = None
    slot = None
    if allocation:
        alloc_id = allocation.id
        slot = allocation.slot

        if allocation.state in (
            AllocationState.RESERVED_PENDING_PAYMENT,
            AllocationState.RESERVED_PAID_PENDING_PICKUP,
        ):
            allocation.mark_expired()
        else:
            allocation.locked_until = None

    logger.info(
        f"[expiry] order={order.id} -> EXPIRED; "
        f"locker_id={locker_id}; "
        f"pickup={pickup_id} -> {pickup.status.value if pickup else 'NONE'}; "
        f"alloc={alloc_id} slot={slot}; "
        f"credit_restored={credit_restored}"
    )

    return {
        "order_id": order.id,
        "allocation_id": alloc_id,
        "slot": slot,
        "region": region,
        "locker_id": locker_id,
    }


def _external_effects(
    *,
    order_id: str,
    allocation_id: Optional[str],
    slot: Optional[int],
    region: str,
    locker_id: Optional[str],
) -> None:
    if slot is not None:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_set_state(
                    region,
                    int(slot),
                    "OUT_OF_STOCK",
                    locker_id=locker_id,
                )
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"[expiry] set_state falhou order={order_id} slot={slot} locker_id={locker_id}: {e}"
                    )
                else:
                    logger.warning(
                        f"[expiry] set_state retry {attempt+1} order={order_id} locker_id={locker_id}: {e}"
                    )

    if allocation_id:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_release(
                    region,
                    allocation_id,
                    locker_id=locker_id,
                )
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"[expiry] locker_release falhou order={order_id} alloc={allocation_id} locker_id={locker_id}: {e}"
                    )
                else:
                    logger.warning(
                        f"[expiry] locker_release retry {attempt+1} order={order_id} locker_id={locker_id}: {e}"
                    )


def run_expiry(db: Session) -> int:
    return run_expiry_once(db)