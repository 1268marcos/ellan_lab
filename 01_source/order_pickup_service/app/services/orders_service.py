import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.pickup_token import PickupToken
from app.services import backend_client

ALLOC_TTL_SEC = int(os.getenv("ALLOC_TTL_SEC", "120"))
PICKUP_WINDOW_SEC = int(os.getenv("PICKUP_WINDOW_SEC", str(2 * 60 * 60)))  # 2h
QR_ROTATE_SEC = int(os.getenv("QR_ROTATE_SEC", "600"))  # 10 min


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _generate_manual_code() -> str:
    """
    MVP: 6 dígitos. (Depois podemos subir para 8 se quiser.)
    """
    # evita leading zeros? aqui permitimos; totem trata como string
    return f"{uuid.uuid4().int % 1_000_000:06d}"


def create_online_order(*, db: Session, user_id: str, region: str, totem_id: str, sku_id: str) -> dict:
    """
    ONLINE:
    - preço via backend (ou fallback DEV)
    - allocate no backend regional
    - persiste order + allocation
    """
    pricing = backend_client.get_sku_pricing(region, sku_id)
    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
    if amount_cents is None:
        raise HTTPException(status_code=502, detail="pricing missing amount_cents/price_cents from backend")

    request_id = str(uuid.uuid4())
    alloc = backend_client.locker_allocate(region, sku_id, ALLOC_TTL_SEC, request_id)

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", ALLOC_TTL_SEC))

    if not allocation_id or slot is None:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    order = Order(
        id=str(uuid.uuid4()),
        user_id=user_id,
        channel=OrderChannel.ONLINE,
        region=region,
        totem_id=totem_id,
        sku_id=sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        pickup_deadline_at=None,  # definido no payment-confirm
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

    return {
        "order_id": order.id,
        "status": order.status.value,
        "amount_cents": order.amount_cents,
        "allocation": {"allocation_id": allocation.id, "slot": allocation.slot, "ttl_sec": ttl_sec},
    }


def confirm_online_payment(*, db: Session, order_id: str, region: str, sale_id: str, paid_at: datetime) -> dict:
    """
    INTERNAL (pós pagamento online):
    - valida order ONLINE
    - seta janela 2h (pickup_deadline_at)
    - commit alocação no backend regional
    - set-state PAID_PENDING_PICKUP
    - cria PickupToken (ponteiro) com token_id (uuid) + manual_code (hash)
    """
    order: Order | None = db.query(Order).filter(Order.id == order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    # coerência
    if order.region != region:
        raise HTTPException(status_code=409, detail="region mismatch for order")

    allocation: Allocation | None = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")

    # janela de retirada 2h a partir do paid_at
    if paid_at.tzinfo is None:
        paid_at = paid_at.replace(tzinfo=timezone.utc)
    pickup_deadline_at = paid_at + timedelta(seconds=PICKUP_WINDOW_SEC)

    # commit no backend (reserva vira firme até o deadline)
    backend_client.locker_commit(order.region, allocation.id, locked_until_iso=pickup_deadline_at.isoformat())

    # marcar slot como pago aguardando retirada (estado “azul” no dashboard)
    backend_client.locker_set_state(order.region, allocation.slot, "PAID_PENDING_PICKUP")

    # cria token ponteiro (token_id = id da linha)
    manual_code = _generate_manual_code()
    token = PickupToken(
        id=str(uuid.uuid4()),
        order_id=order.id,
        token_hash=_sha256(manual_code),  # usado no fallback manual
        expires_at=pickup_deadline_at.replace(tzinfo=None),  # sqlite naive
        used_at=None,
    )
    db.add(token)

    # atualiza order/allocation
    order.status = OrderStatus.PAID_PENDING_PICKUP
    order.pickup_deadline_at = pickup_deadline_at.replace(tzinfo=None)  # sqlite naive
    allocation.state = AllocationState.RESERVED_PENDING_PICKUP
    allocation.locked_until = pickup_deadline_at.replace(tzinfo=None)

    db.commit()

    # resposta para integração (não é para o cliente final)
    return {
        "ok": True,
        "order_id": order.id,
        "pickup_id": order.id,          # MVP: pickup_id == order_id
        "token_id": token.id,           # ponteiro (vai no QR)
        "expires_at": pickup_deadline_at.isoformat(),
        "qr_rotate_sec": QR_ROTATE_SEC,
        "manual_code": manual_code,     # mostrar ao cliente no site/app (fallback)
    }