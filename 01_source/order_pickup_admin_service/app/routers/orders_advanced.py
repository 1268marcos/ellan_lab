from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    GiftPickupCreateIn,
    GiftPickupListOut,
    GiftPickupOut,
    GiftPickupUpdateIn,
    ItemSubstitutionCreateIn,
    ItemSubstitutionListOut,
    ItemSubstitutionOut,
    ItemSubstitutionUpdateIn,
    NotificationLogListOut,
    OpsHoldCreateIn,
    OpsHoldListOut,
    OpsHoldOut,
    OpsHoldReleaseIn,
    OrderReturnCreateIn,
    OrderReturnListOut,
    OrderReturnOut,
    OrderReturnUpdateIn,
    PaymentReconcileRunIn,
    PaymentReconciliationListOut,
    PaymentSyncIn,
    PaymentTransactionListOut,
    PaymentTransactionOut,
)
from app.services import orders_advanced_service
from app.services.payments_bridge_service import list_payment_transactions, sync_from_payments_admin

router = APIRouter(tags=["orders-advanced"])


@router.get("/order-returns", response_model=OrderReturnListOut)
def list_returns(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OrderReturnListOut:
    items, total = orders_advanced_service.list_returns(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return OrderReturnListOut(items=items, total=total)


@router.post("/order-returns", response_model=OrderReturnOut, status_code=status.HTTP_201_CREATED)
def create_return(body: OrderReturnCreateIn, db: Session = Depends(get_db)) -> OrderReturnOut:
    return orders_advanced_service.create_return(db, body)


@router.patch("/order-returns/{return_id}", response_model=OrderReturnOut)
def update_return(
    return_id: str, body: OrderReturnUpdateIn, db: Session = Depends(get_db)
) -> OrderReturnOut:
    return orders_advanced_service.update_return(db, return_id, body)


@router.get("/order-notifications", response_model=NotificationLogListOut)
def list_notifications(
    order_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> NotificationLogListOut:
    items, total = orders_advanced_service.list_notifications(
        db, order_id=order_id, channel=channel, limit=limit, offset=offset
    )
    return NotificationLogListOut(items=items, total=total)


@router.get("/payment-reconciliation", response_model=PaymentReconciliationListOut)
def list_reconciliation(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaymentReconciliationListOut:
    items, total = orders_advanced_service.list_payment_reconciliation(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return PaymentReconciliationListOut(items=items, total=total)


@router.post("/payment-reconciliation/run", response_model=dict)
def run_reconciliation(body: PaymentReconcileRunIn, db: Session = Depends(get_db)) -> dict:
    return orders_advanced_service.run_payment_reconciliation(db, order_id=body.order_id)


@router.get("/order-holds", response_model=OpsHoldListOut)
def list_holds(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OpsHoldListOut:
    items, total = orders_advanced_service.list_holds(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return OpsHoldListOut(items=items, total=total)


@router.post("/order-holds", response_model=OpsHoldOut, status_code=status.HTTP_201_CREATED)
def create_hold(body: OpsHoldCreateIn, db: Session = Depends(get_db)) -> OpsHoldOut:
    return orders_advanced_service.create_hold(db, body)


@router.post("/order-holds/{hold_id}/release", response_model=OpsHoldOut)
def release_hold(hold_id: str, body: OpsHoldReleaseIn, db: Session = Depends(get_db)) -> OpsHoldOut:
    return orders_advanced_service.release_hold(db, hold_id, body.released_by)


@router.get("/item-substitutions", response_model=ItemSubstitutionListOut)
def list_substitutions(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ItemSubstitutionListOut:
    items, total = orders_advanced_service.list_substitutions(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return ItemSubstitutionListOut(items=items, total=total)


@router.post("/item-substitutions", response_model=ItemSubstitutionOut, status_code=status.HTTP_201_CREATED)
def create_substitution(body: ItemSubstitutionCreateIn, db: Session = Depends(get_db)) -> ItemSubstitutionOut:
    return orders_advanced_service.create_substitution(db, body)


@router.patch("/item-substitutions/{sub_id}", response_model=ItemSubstitutionOut)
def update_substitution(
    sub_id: str, body: ItemSubstitutionUpdateIn, db: Session = Depends(get_db)
) -> ItemSubstitutionOut:
    return orders_advanced_service.update_substitution(db, sub_id, body)


@router.get("/gift-pickups", response_model=GiftPickupListOut)
def list_gifts(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> GiftPickupListOut:
    items, total = orders_advanced_service.list_gift_pickups(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return GiftPickupListOut(items=items, total=total)


@router.post("/gift-pickups", response_model=GiftPickupOut, status_code=status.HTTP_201_CREATED)
def create_gift(body: GiftPickupCreateIn, db: Session = Depends(get_db)) -> GiftPickupOut:
    return orders_advanced_service.create_gift_pickup(db, body)


@router.patch("/gift-pickups/{gift_id}", response_model=GiftPickupOut)
def update_gift(gift_id: str, body: GiftPickupUpdateIn, db: Session = Depends(get_db)) -> GiftPickupOut:
    return orders_advanced_service.update_gift_pickup(db, gift_id, body)


@router.get("/payment-transactions", response_model=PaymentTransactionListOut)
def list_payment_tx(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaymentTransactionListOut:
    rows, total = list_payment_transactions(db, order_id=order_id, status=status, limit=limit, offset=offset)
    return PaymentTransactionListOut(
        items=[PaymentTransactionOut.model_validate(r) for r in rows],
        total=total,
    )


@router.post("/payment-transactions/sync", response_model=dict)
def sync_payment_tx(body: PaymentSyncIn, db: Session = Depends(get_db)) -> dict:
    return sync_from_payments_admin(db, order_id=body.order_id)
