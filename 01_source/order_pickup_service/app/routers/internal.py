# 01_source/order_pickup_service/app/routers/internal.py
# Router: /internal/* (protegido por X-Internal-Token)
#
# Responsabilidade:
# - receber confirmação de pagamento (gateway -> order_pickup_service)
# - executar efeitos no backend do totem (commit / open / light / set-state)
# - permitir operações internas de suporte (release/cancel, set-state, status, health)
#
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.internal_auth import require_internal_token

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState

# ✅ Ajuste: mantenho o que você disse que já existe:
from app.schemas.internal import InternalPaymentApprovedIn as PaymentConfirmIn

from app.services import backend_client

router = APIRouter(prefix="/internal", tags=["internal"])

PICKUP_WINDOW_HOURS = 2


# =========================
# Helpers
# =========================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_allocation(db: Session, order_id: str) -> Allocation:
    allocation = db.query(Allocation).filter(Allocation.order_id == order_id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")
    return allocation


def _ensure_order(db: Session, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


# =========================
# 0) Healthcheck interno
# =========================

@router.get("/health")
def internal_health(_=Depends(require_internal_token)):
    return {"ok": True, "service": "order_pickup_service", "time": _utc_now().isoformat()}


# =========================
# 1) Confirmação de pagamento (principal)
# =========================

@router.post("/orders/{order_id}/payment-confirm")
def payment_confirm(
    order_id: str,
    payload: PaymentConfirmIn,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    """
    Quando o gateway confirmar o pagamento, esse endpoint finaliza a transição:

    ONLINE:
      PAYMENT_PENDING -> PAID_PENDING_PICKUP
      - define pickup_deadline_at = now + 2h
      - allocation: RESERVED_PENDING_PAYMENT -> RESERVED_PAID_PENDING_PICKUP
      - locker_commit(... locked_until=deadline)

    KIOSK:
      PAYMENT_PENDING -> PICKED_UP (fluxo simples)
      - locker_commit(... locked_until=None)
      - light_on + open
      - (se quiser 2 fases depois, a gente muda: PAID_PENDING_PICKUP -> PICKED_UP ao "gaveta fechou")
    """
    order = _ensure_order(db, order_id)

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    allocation = _ensure_allocation(db, order.id)

    now = _utc_now()

    # rastreabilidade de pagamento
    # (mantém compatível com seu model; ajuste nomes se necessário)
    # order.gateway_transaction_id = payload.gateway_transaction_id
    # oficial
    order.gateway_transaction_id = payload.transaction_id
    order.paid_at = now

    if order.channel == OrderChannel.ONLINE:
        deadline = now + timedelta(hours=PICKUP_WINDOW_HOURS)

        order.pickup_deadline_at = deadline
        order.status = OrderStatus.PAID_PENDING_PICKUP

        allocation.state = AllocationState.RESERVED_PAID_PENDING_PICKUP
        allocation.locked_until = deadline.replace(tzinfo=None)  # DB naive (como você já faz)

        # backend (totem): commit com locked_until
        backend_client.locker_commit(order.region, allocation.id, deadline.isoformat())

    else:
        # KIOSK / PRESENCIAL:
        order.pickup_deadline_at = None

        # ✅ “fluxo simples”: abre já e marca como pick-up concluído
        order.status = OrderStatus.PICKED_UP
        allocation.state = AllocationState.OPENED_FOR_PICKUP

        backend_client.locker_commit(order.region, allocation.id, None)
        backend_client.locker_light_on(order.region, allocation.slot)
        backend_client.locker_open(order.region, allocation.slot)

        # opcional (se seu backend suportar): já deixar cinza pós-retirada
        # backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "channel": order.channel.value,
        "status": order.status.value,
        "slot": allocation.slot,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
    }


# =========================
# 2) Release / cancel interno (rollback)
# =========================

@router.post("/orders/{order_id}/release")
def release_order(
    order_id: str,
    reason: Optional[str] = None,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    """
    Use quando:
    - pagamento falhou
    - timeout
    - rollback manual

    Faz:
    - marca Order como EXPIRED (ou você pode criar CANCELLED)
    - allocation -> RELEASED
    - chama backend: locker_release(allocation_id)
    """
    order = _ensure_order(db, order_id)
    allocation = _ensure_allocation(db, order.id)

    # evita liberar coisa já finalizada
    if order.status in (OrderStatus.PICKED_UP,):
        raise HTTPException(status_code=409, detail=f"cannot release in state: {order.status.value}")

    # efeito no backend
    try:
        backend_client.locker_release(order.region, allocation.id)
    except Exception as e:
        # aqui eu prefiro falhar: release não pode “fingir” que deu certo
        raise HTTPException(status_code=502, detail=f"backend release failed: {str(e)}")

    # efeito local
    order.status = OrderStatus.EXPIRED  # se você tiver CANCELLED, troque aqui
    allocation.state = AllocationState.RELEASED
    allocation.locked_until = None

    # (opcional) salvar reason em campo próprio se existir
    # order.cancel_reason = reason

    db.commit()
    return {"ok": True, "order_id": order.id, "status": order.status.value, "reason": reason}


# =========================
# 3) Set-state interno de slot (OUT_OF_STOCK etc.)
# =========================

@router.post("/slots/{slot}/set-state")
def internal_set_slot_state(
    slot: int,
    state: str,
    region: str,
    _=Depends(require_internal_token),
):
    """
    Endpoint interno para centralizar “cinza / aguardar reposição”.

    Exemplo:
      POST /internal/slots/12/set-state?region=PT&state=OUT_OF_STOCK
    """
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be between 1 and 24")
    if region not in ("SP", "PT"):
        raise HTTPException(status_code=400, detail="region must be SP or PT")

    try:
        resp = backend_client.locker_set_state(region, slot, state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"backend set-state failed: {str(e)}")

    return {"ok": True, "region": region, "slot": slot, "state": state, "backend_response": resp}


# =========================
# 4) Status interno (debug rápido)
# =========================

@router.get("/orders/{order_id}/status")
def internal_order_status(
    order_id: str,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    """
    Para debug: devolve status do Order + Allocation.
    """
    order = _ensure_order(db, order_id)
    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()

    return {
        "ok": True,
        "order": {
            "id": order.id,
            "channel": order.channel.value,
            "region": order.region,
            "totem_id": order.totem_id,
            "sku_id": getattr(order, "sku_id", None),
            "status": order.status.value,
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
            "gateway_transaction_id": getattr(order, "gateway_transaction_id", None),
        },
        "allocation": None if not allocation else {
            "id": allocation.id,
            "slot": allocation.slot,
            "state": allocation.state.value,
            "locked_until": allocation.locked_until.isoformat() if allocation.locked_until else None,
        }
    }