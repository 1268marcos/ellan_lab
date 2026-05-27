from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.credit import Credit, CreditStatus
from app.models.order import Order
from app.models.pickup import Pickup, PickupStatus
from app.services import backend_client
from app.services.wallet_credits import restore_credit_after_failed_order_creation


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class OrderReconciliationResult:
    slot_release_attempted: bool
    slot_release_success: bool
    slot_release_error: str | None
    credit_restore_attempted: bool
    credit_restore_success: bool
    credit_restore_error: str | None
    allocation_id: str | None = None
    allocation_state: str | None = None

    @property
    def slot_release_ok(self) -> bool:
        """Alias legado para respostas HTTP existentes."""
        return self.slot_release_success

    @property
    def credit_restored(self) -> bool:
        """Alias legado para respostas HTTP existentes."""
        return self.credit_restore_success

    def to_payload_dict(self) -> dict:
        return {
            "slot_release_attempted": self.slot_release_attempted,
            "slot_release_success": self.slot_release_success,
            "slot_release_error": self.slot_release_error,
            "credit_restore_attempted": self.credit_restore_attempted,
            "credit_restore_success": self.credit_restore_success,
            "credit_restore_error": self.credit_restore_error,
            "allocation_id": self.allocation_id,
            "allocation_state": self.allocation_state,
            "recorded_at": _utc_now().isoformat(),
        }


def compensation_steps_for_reason(reason: str) -> tuple[bool, bool]:
    """
    Mapeia ``reconciliation_pending.reason`` para passos a reexecutar.

    Returns:
        Tupla ``(run_slot_release, run_credit_restore)``.
    """
    reason_norm = str(reason or "").strip().lower()
    if reason_norm == "slot_release_failed":
        return True, False
    if reason_norm == "credit_restore_failed":
        return False, True
    return True, True


def pending_step_succeeded(*, reason: str, result: OrderReconciliationResult) -> bool:
    """
    Indica se o passo alvo desta pendência foi concluído com sucesso.

    Falha em outro passo (não executado nesta retentativa) não impede DONE.
    """
    reason_norm = str(reason or "").strip().lower()
    if reason_norm == "slot_release_failed":
        return result.slot_release_attempted and result.slot_release_success
    if reason_norm == "credit_restore_failed":
        return result.credit_restore_attempted and result.credit_restore_success
    slot_ok = (not result.slot_release_attempted) or result.slot_release_success
    credit_ok = (not result.credit_restore_attempted) or result.credit_restore_success
    return slot_ok and credit_ok


def _order_credit_application(order: Order) -> dict | None:
    meta = getattr(order, "order_metadata", None)
    if not isinstance(meta, Mapping):
        return None
    cap = meta.get("credit_application")
    return dict(cap) if isinstance(cap, Mapping) else None


def order_has_applied_credit(order: Order) -> bool:
    cap = _order_credit_application(order)
    return bool(cap and cap.get("applied") and cap.get("credit_id"))


def restore_checkout_credit_if_needed(*, db: Session, order: Order) -> bool:
    return bool(
        restore_credit_after_failed_order_creation(
            db=db,
            order_metadata=getattr(order, "order_metadata", None),
        )
    )


def mark_allocation_released_locally(*, allocation: Allocation | None) -> str | None:
    if not allocation:
        return None
    allocation.mark_released()
    return allocation.state.value if allocation.state else None


def resolve_latest_allocation(db: Session, *, order: Order) -> Allocation | None:
    allocation = None
    if getattr(order, "allocation_id", None):
        allocation = db.query(Allocation).filter(Allocation.id == order.allocation_id).first()
    if allocation is None:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order.id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )
    return allocation


def resolve_latest_pickup(db: Session, *, order: Order) -> Pickup | None:
    return (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )


def _credit_restore_already_satisfied(*, db: Session, order: Order) -> bool:
    cap = _order_credit_application(order)
    if not cap or not cap.get("credit_id"):
        return False
    credit = db.get(Credit, str(cap["credit_id"]))
    return credit is not None and credit.status == CreditStatus.AVAILABLE


def _attempt_slot_release(
    *,
    order: Order,
    allocation: Allocation | None,
) -> tuple[bool, bool, str | None]:
    if not allocation:
        return False, False, None
    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
        mark_allocation_released_locally(allocation=allocation)
        return True, True, None
    except Exception as exc:
        return True, False, str(exc)


def _attempt_credit_restore(
    *,
    db: Session,
    order: Order,
) -> tuple[bool, bool, str | None]:
    if not order_has_applied_credit(order):
        return False, False, None
    try:
        if restore_checkout_credit_if_needed(db=db, order=order):
            return True, True, None
        if _credit_restore_already_satisfied(db=db, order=order):
            return True, True, None
        return True, False, "credit_not_restored"
    except Exception as exc:
        return True, False, str(exc)


def _record_reconciliation_pending_failures(
    *,
    db: Session,
    order: Order,
    allocation: Allocation | None,
    pickup: Pickup | None,
    result: OrderReconciliationResult,
) -> None:
    try:
        from app.services.reconciliation_pending_service import enqueue_reconciliation_pending

        common_payload = {
            "order_id": order.id,
            "region": getattr(order, "region", None),
            "locker_id": getattr(order, "totem_id", None),
            "allocation_id": allocation.id if allocation else None,
            "pickup_id": pickup.id if pickup else None,
            "compensation_result": result.to_payload_dict(),
        }
        if result.slot_release_error:
            enqueue_reconciliation_pending(
                db=db,
                order_id=order.id,
                reason="slot_release_failed",
                payload={
                    **common_payload,
                    "error": result.slot_release_error,
                    "retry_step": "slot_release",
                },
            )
        if result.credit_restore_error:
            enqueue_reconciliation_pending(
                db=db,
                order_id=order.id,
                reason="credit_restore_failed",
                payload={
                    **common_payload,
                    "error": result.credit_restore_error,
                    "retry_step": "credit_restore",
                },
            )
    except Exception:
        # Falha de enfileiramento não deve interromper o fluxo síncrono.
        pass


def reconcile_order_compensation(
    *,
    db: Session,
    order: Order,
    allocation: Allocation | None,
    pickup: Pickup | None,
    cancel_reason: str = "public_order_cancelled",
    record_pending_on_failure: bool = True,
    run_slot_release: bool = True,
    run_credit_restore: bool = True,
) -> OrderReconciliationResult:
    """
    Executa compensação de cancelamento/reconciliação por passos independentes.

    Cada passo (liberação de slot, restauração de crédito) reporta sucesso/erro
    separadamente. Falha parcial enfileira pendências distintas por ``reason``,
    permitindo retentativas seletivas no worker assíncrono.
    """
    slot_release_attempted = False
    slot_release_success = False
    slot_release_error: str | None = None

    if run_slot_release:
        slot_release_attempted, slot_release_success, slot_release_error = _attempt_slot_release(
            order=order,
            allocation=allocation,
        )

    credit_restore_attempted = False
    credit_restore_success = False
    credit_restore_error: str | None = None

    if run_credit_restore:
        credit_restore_attempted, credit_restore_success, credit_restore_error = (
            _attempt_credit_restore(db=db, order=order)
        )

    if pickup and pickup.status != PickupStatus.CANCELLED:
        pickup.mark_cancelled(cancel_reason)

    result = OrderReconciliationResult(
        slot_release_attempted=slot_release_attempted,
        slot_release_success=slot_release_success,
        slot_release_error=slot_release_error,
        credit_restore_attempted=credit_restore_attempted,
        credit_restore_success=credit_restore_success,
        credit_restore_error=credit_restore_error,
        allocation_id=allocation.id if allocation else None,
        allocation_state=allocation.state.value if allocation and allocation.state else None,
    )

    if record_pending_on_failure and (result.slot_release_error or result.credit_restore_error):
        _record_reconciliation_pending_failures(
            db=db,
            order=order,
            allocation=allocation,
            pickup=pickup,
            result=result,
        )

    return result
