# 01_source/order_pickup_service/app/routers/kiosk.py
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.schemas.kiosk import (
    KioskOrderCreateIn,
    KioskOrderOut,
    KioskCustomerIdentifyIn,
    KioskIdentifyOut,
    KioskPaymentApprovedOut,
)
from app.services import backend_client
from app.services.antifraud_kiosk import check_kiosk_antifraud

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

# janela curta só pra “segurar” enquanto paga no totem
ALLOC_TTL_SEC = 120


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
    - Retorna slot e amount_cents para UI do totem seguir para pagamento no gateway
    """

    # 0) antifraude leve (rate limit)
    check_kiosk_antifraud(
        db=db,
        request=request,
        totem_id=payload.totem_id,
        region=payload.region,
        device_fingerprint=x_device_fingerprint,
    )

    # 1) preço vem do backend (fonte de verdade)
    pricing = backend_client.get_sku_pricing(payload.region, payload.sku_id)
    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
    if amount_cents is None:
        raise HTTPException(status_code=502, detail="pricing missing amount_cents/price_cents from backend")

    # 2) allocate no backend do totem
    request_id = str(uuid.uuid4())
    alloc = backend_client.locker_allocate(payload.region, payload.sku_id, ALLOC_TTL_SEC, request_id)
    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", ALLOC_TTL_SEC))
    if not allocation_id or slot is None:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    # 3) persiste order + allocation
    order = Order(
        id=str(uuid.uuid4()),
        user_id=None,  # guest
        channel=OrderChannel.KIOSK,
        region=payload.region,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        guest_phone=None,
        guest_email=None,
        pickup_deadline_at=None,  # presencial não tem janela 2h
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

    return KioskOrderOut(
        order_id=order.id,
        status=order.status.value,
        slot=allocation.slot,
        amount_cents=order.amount_cents,
        message=f"Reserva criada. Conclua o pagamento para liberar a gaveta {allocation.slot}. (TTL {ttl_sec}s)",
    )


@router.post("/orders/{order_id}/payment-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    CHAMADO APÓS O PAGAMENTO SER APROVADO (no totem).
    Aqui é o “dispense”: acende, abre, marca OUT_OF_STOCK.
    """

    order = db.query(Order).filter(Order.id == order_id, Order.channel == OrderChannel.KIOSK).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")

    # 1) commit (confirma alocação no backend do totem)
    backend_client.locker_commit(order.region, allocation.id, locked_until_iso=None)

    # 2) abre + led + marca out_of_stock
    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    # 3) atualiza status interno
    order.status = OrderStatus.DISPENSED
    allocation.state = AllocationState.OPENED_FOR_PICKUP
    db.commit()

    return KioskPaymentApprovedOut(
        order_id=order.id,
        slot=allocation.slot,
        status=order.status.value,
        message=f"Espere a porta abrir e pegue o seu bolo na gaveta {allocation.slot}.",
    )


@router.post("/identify", response_model=KioskIdentifyOut)
def kiosk_identify_customer(
    payload: KioskCustomerIdentifyIn,
    db: Session = Depends(get_db),
):
    """
    “Upgrade” do Guest:
    Depois do pagamento, a UI pode perguntar:
    'Quer recibo e benefícios?'
    Se sim, chama aqui com phone/email (opcional).
    """
    order = db.query(Order).filter(Order.id == payload.order_id, Order.channel == OrderChannel.KIOSK).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    # regra simples: permitir identificar após pagar (ou dispense)
    if order.status not in (OrderStatus.PAID_PENDING_PICKUP, OrderStatus.DISPENSED, OrderStatus.PICKED_UP):
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    # grava contato (opcional)
    if payload.phone:
        order.guest_phone = payload.phone.strip()
    if payload.email:
        order.guest_email = str(payload.email).strip().lower()

    db.commit()

    return KioskIdentifyOut(ok=True, message="Dados registrados. Recibo/benefícios poderão ser associados a este pedido.")