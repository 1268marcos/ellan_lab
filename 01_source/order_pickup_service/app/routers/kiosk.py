# 01_source/order_pickup_service/app/routers/kiosk.py
# Aqui faz pedido KIOSK
# Router: /orders (KIOSK)
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.schemas.kiosk import (
    KioskCustomerIdentifyIn,
    KioskIdentifyOut,
    KioskOrderCreateIn,
    KioskOrderOut,
    KioskPaymentApprovedOut,
)
from app.services import backend_client
from app.services.antifraud_kiosk import check_kiosk_antifraud
from app.services.lifecycle_integration import (
    cancel_prepayment_timeout_deadline,
    register_prepayment_timeout_deadline,
)

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

# janela curta só pra “segurar” enquanto paga no totem
ALLOC_TTL_SEC = 120


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_allocation_by_order(db: Session, order_id: str) -> Allocation | None:
    return db.query(Allocation).filter(Allocation.order_id == order_id).first()


@router.post("/orders", response_model=KioskOrderOut)
def kiosk_create_order(
    payload: KioskOrderCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    x_device_fingerprint: str | None = Header(default=None, alias="X-Device-Fingerprint"),
):
    """
    PRESENCIAL:
    - Guest por padrão
    - Reserva slot por 120s (tempo do pagamento)
    - Retorna slot e amount_cents para UI do totem seguir para pagamento
    """

    check_kiosk_antifraud(
        db=db,
        request=request,
        totem_id=payload.totem_id,
        region=payload.region,
        device_fingerprint=x_device_fingerprint,
    )

    pricing = backend_client.get_sku_pricing(payload.region, payload.sku_id)
    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
    if amount_cents is None:
        raise HTTPException(status_code=502, detail="pricing missing amount_cents/price_cents from backend")

    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            payload.region,
            payload.sku_id,
            ALLOC_TTL_SEC,
            request_id,
            payload.desired_slot,
        )
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else 502

        backend_detail = None
        if e.response is not None:
            try:
                backend_detail = e.response.json()
            except Exception:
                backend_detail = e.response.text

        if status == 409:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "DESIRED_SLOT_UNAVAILABLE",
                    "message": "A gaveta escolhida não está disponível no momento.",
                    "desired_slot": payload.desired_slot,
                    "sku_id": payload.sku_id,
                    "region": payload.region,
                    "backend_detail": backend_detail,
                },
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao alocar gaveta no backend regional.",
                "desired_slot": payload.desired_slot,
                "sku_id": payload.sku_id,
                "region": payload.region,
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", ALLOC_TTL_SEC))

    if not allocation_id or slot is None:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    order = Order(
        id=str(uuid.uuid4()),
        user_id=None,
        channel=OrderChannel.KIOSK,
        region=payload.region,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        payment_method=payload.payment_method.value,
        guest_phone=None,
        guest_email=None,
        pickup_deadline_at=None,
    )
    db.add(order)
    db.flush()

    allocation = Allocation(
        id=allocation_id,
        order_id=order.id,
        slot=int(slot),
        state=AllocationState.RESERVED_PENDING_PAYMENT,
        locked_until=None,
    )
    db.add(allocation)
    db.commit()
    db.refresh(order)
    db.refresh(allocation)

    try:
        register_prepayment_timeout_deadline(
            order_id=order.id,
            order_channel=order.channel.value,
            region_code=order.region,
            slot_id=str(allocation.slot),
            machine_id=order.totem_id,
            created_at=order.created_at,
        )
    except LifecycleClientError:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_DEADLINE_REGISTER_FAILED",
                "message": "Pedido criado localmente, mas falhou ao registrar o deadline de pré-pagamento.",
                "order_id": order.id,
                "channel": order.channel.value,
                "region": order.region,
            },
        )

    return KioskOrderOut(
        order_id=order.id,
        status=order.status.value,
        slot=allocation.slot,
        amount_cents=order.amount_cents,
        payment_method=order.payment_method,
        allocation_id=allocation.id,
        ttl_sec=ttl_sec,
        message=f"Reserva criada. Conclua o pagamento para liberar a gaveta {allocation.slot}.",
    )


@router.post("/orders/{order_id}/payment-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    CHAMADO APÓS O PAGAMENTO SER APROVADO NO KIOSK.
    Fluxo KIOSK:
    - confirma alocação
    - liga led
    - abre gaveta
    - marca slot como OUT_OF_STOCK
    - pedido vira DISPENSED
    """

    order = db.query(Order).filter(Order.id == order_id, Order.channel == OrderChannel.KIOSK).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    allocation = _get_allocation_by_order(db, order.id)
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")

    if order.status == OrderStatus.DISPENSED:
        return KioskPaymentApprovedOut(
            order_id=order.id,
            slot=allocation.slot,
            status=order.status.value,
            allocation_id=allocation.id,
            payment_method=order.payment_method,
            message="Pagamento já aprovado anteriormente.",
        )

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    try:
        backend_client.locker_commit(order.region, allocation.id, locked_until_iso=None)
        backend_client.locker_light_on(order.region, allocation.slot)
        backend_client.locker_open(order.region, allocation.slot)
        backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else 502

        backend_detail = None
        if e.response is not None:
            try:
                backend_detail = e.response.json()
            except Exception:
                backend_detail = e.response.text

        raise HTTPException(
            status_code=502,
            detail={
                "type": "KIOSK_PAYMENT_APPROVAL_BACKEND_FAILED",
                "message": "Falha operacional ao concluir o fluxo KIOSK no backend regional.",
                "order_id": order.id,
                "allocation_id": allocation.id,
                "region": order.region,
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "KIOSK_PAYMENT_APPROVAL_BACKEND_FAILED",
                "message": "Falha operacional ao concluir o fluxo KIOSK no backend regional.",
                "order_id": order.id,
                "allocation_id": allocation.id,
                "region": order.region,
                "error": str(e),
            },
        )

    order.paid_at = _utc_now_naive()
    order.status = OrderStatus.DISPENSED
    allocation.state = AllocationState.OPENED_FOR_PICKUP
    allocation.locked_until = None
    db.commit()
    db.refresh(order)
    db.refresh(allocation)

    try:
        cancel_prepayment_timeout_deadline(order_id=order.id)
    except LifecycleClientError:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_DEADLINE_CANCEL_FAILED",
                "message": "Pagamento confirmado localmente, mas falhou ao cancelar o deadline de pré-pagamento.",
                "order_id": order.id,
                "channel": order.channel.value,
                "region": order.region,
            },
        )

    return KioskPaymentApprovedOut(
        order_id=order.id,
        slot=allocation.slot,
        status=order.status.value,
        allocation_id=allocation.id,
        payment_method=order.payment_method,
        message=f"Pagamento aprovado. Retire o produto na gaveta {allocation.slot}.",
    )


@router.post("/identify", response_model=KioskIdentifyOut)
def kiosk_identify_customer(
    payload: KioskCustomerIdentifyIn,
    db: Session = Depends(get_db),
):
    """
    Upgrade opcional do guest após pagamento:
    registrar contato para recibo/benefícios.
    """
    order = db.query(Order).filter(Order.id == payload.order_id, Order.channel == OrderChannel.KIOSK).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if order.status not in (OrderStatus.DISPENSED, OrderStatus.PICKED_UP):
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    if payload.phone:
        order.guest_phone = payload.phone.strip()
        order.receipt_phone = payload.phone.strip()

    if payload.email:
        normalized_email = str(payload.email).strip().lower()
        order.guest_email = normalized_email
        order.receipt_email = normalized_email

    db.commit()

    return KioskIdentifyOut(
        ok=True,
        message="Dados registrados. Recibo/benefícios poderão ser associados a este pedido.",
    )