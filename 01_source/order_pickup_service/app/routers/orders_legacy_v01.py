# 01_source/order_pickup_service/app/routers/orders.py
# Router: /orders (ONLINE)
# Aqui faz pedido ONLINE
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.auth_dev import get_current_user_or_dev
from app.core.config import settings
from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds
from app.models.allocation import Allocation, AllocationState
from app.models.order import CardType, Order, OrderChannel, OrderStatus, PaymentMethod
from app.models.pickup import Pickup
from app.schemas.orders import CreateOrderIn, OrderListItemOut, OrderListOut, OrderOut
from app.services import backend_client
from app.services.lifecycle_integration import register_prepayment_timeout_deadline

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)


def _normalize_upper_list(values: list[str] | None) -> list[str]:
    return [str(v).strip().upper() for v in (values or []) if str(v).strip()]


def _resolve_online_prepayment_ttl_sec(*, region: str, payment_method: str) -> int:
    ttl_sec = resolve_prepayment_timeout_seconds(
        region_code=region,
        order_channel=OrderChannel.ONLINE.value,
        payment_method=payment_method,
    )

    if int(ttl_sec) <= 0:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "ONLINE_PAYMENT_TTL_POLICY_INVALID",
                "message": "O TTL configurado deve ser maior que zero.",
                "region": str(region or "").strip().upper(),
                "channel": OrderChannel.ONLINE.value,
                "payment_method": str(payment_method or "").strip().upper(),
                "ttl_value": ttl_sec,
            },
        )

    return int(ttl_sec)


def _resolve_payment_method_enum(method_value: str) -> PaymentMethod:
    try:
        return PaymentMethod(method_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_PAYMENT_METHOD",
                "message": f"Método de pagamento não suportado no pedido ONLINE: {method_value}",
            },
        ) from exc


def _resolve_card_type_enum(card_type_value: str | None) -> CardType | None:
    if not card_type_value:
        return None

    try:
        return CardType(card_type_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_CARD_TYPE",
                "message": f"Tipo de cartão inválido: {card_type_value}",
            },
        ) from exc


def _validate_online_locker_context(payload: CreateOrderIn) -> dict:
    locker = backend_client.get_locker_registry_item(payload.totem_id)

    if not locker:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {payload.totem_id}",
                "locker_id": payload.totem_id,
                "retryable": False,
            },
        )

    if not bool(locker.get("active", False)):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_INACTIVE",
                "message": "O locker informado está inativo.",
                "locker_id": payload.totem_id,
                "retryable": False,
            },
        )

    locker_region = str(locker.get("region") or "").strip().upper()
    payload_region = payload.region.value.strip().upper()

    if locker_region != payload_region:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_REGION_MISMATCH",
                "message": "O locker informado não pertence à região do pedido.",
                "locker_id": payload.totem_id,
                "payload_region": payload_region,
                "locker_region": locker_region,
                "retryable": False,
            },
        )

    channels = _normalize_upper_list(locker.get("channels"))
    if "ONLINE" not in channels:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": "O locker informado não aceita pedidos no canal ONLINE.",
                "locker_id": payload.totem_id,
                "allowed_channels": channels,
                "retryable": False,
            },
        )

    payment_methods = _normalize_upper_list(locker.get("payment_methods"))
    requested_method = payload.payment_method.value.strip().upper()

    if requested_method not in payment_methods:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_PAYMENT_METHOD_NOT_ALLOWED",
                "message": "O método de pagamento informado não é permitido para este locker.",
                "locker_id": payload.totem_id,
                "payment_method": requested_method,
                "allowed_payment_methods": payment_methods,
                "retryable": False,
            },
        )

    return locker


def _compensate_failed_online_creation(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
) -> None:
    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
    except Exception:
        logger.exception(
            "online_order_compensation_release_failed",
            extra={
                "order_id": order.id,
                "allocation_id": allocation.id,
                "region": order.region,
                "locker_id": order.totem_id,
            },
        )
        raise

    try:
        db.delete(allocation)
        db.delete(order)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "online_order_compensation_db_failed",
            extra={
                "order_id": order.id,
                "allocation_id": allocation.id,
            },
        )
        raise


@router.post("", response_model=OrderOut)
def create_order(
    payload: CreateOrderIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    _validate_online_locker_context(payload)

    payment_method = _resolve_payment_method_enum(payload.payment_method.value)
    card_type = _resolve_card_type_enum(
        payload.card_type.value if payload.card_type else None
    )

    alloc_ttl_sec = _resolve_online_prepayment_ttl_sec(
        region=payload.region.value,
        payment_method=payment_method.value,
    )

    amount_cents = None

    if payload.amount_cents is not None:
        if int(payload.amount_cents) <= 0:
            raise HTTPException(status_code=400, detail="amount_cents must be > 0")
        amount_cents = int(payload.amount_cents)

    if amount_cents is None:
        try:
            pricing = backend_client.get_sku_pricing(
                payload.region.value,
                payload.sku_id,
                locker_id=payload.totem_id,
            )
        except HTTPError as e:
            if (
                e.response is not None
                and e.response.status_code == 404
                and settings.dev_allow_unknown_sku
            ):
                pricing = {"amount_cents": settings.dev_default_price_cents}
            else:
                raise

        amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
        if amount_cents is None:
            raise HTTPException(
                status_code=502,
                detail="pricing missing amount_cents/price_cents from backend",
            )

    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            payload.region.value,
            payload.sku_id,
            alloc_ttl_sec,
            request_id,
            payload.desired_slot,
            locker_id=payload.totem_id,
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
                    "message": "A gaveta escolhida não está disponível para reserva.",
                    "desired_slot": payload.desired_slot,
                    "region": payload.region.value,
                    "locker_id": payload.totem_id,
                    "backend_detail": backend_detail,
                },
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao alocar gaveta no backend.",
                "region": payload.region.value,
                "locker_id": payload.totem_id,
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", alloc_ttl_sec))

    if not allocation_id or slot is None:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    resolved_user_id = getattr(user, "id", None)
    resolved_user_id = str(resolved_user_id) if resolved_user_id is not None else None

    order = Order(
        id=str(uuid.uuid4()),
        user_id=resolved_user_id,
        channel=OrderChannel.ONLINE,
        region=payload.region.value,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        payment_method=payment_method,
        card_type=card_type,
        guest_phone=payload.customer_phone,
    )
    db.add(order)
    db.flush()

    allocation = Allocation(
        id=allocation_id,
        order_id=order.id,
        locker_id=payload.totem_id,
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
            payment_method=order.payment_method.value if order.payment_method else None,
        )
    except LifecycleClientError:
        try:
            _compensate_failed_online_creation(
                db=db,
                order=order,
                allocation=allocation,
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "LIFECYCLE_DEADLINE_REGISTER_FAILED_WITH_COMPENSATION_ERROR",
                    "message": "Pedido criado localmente, falhou o registro do deadline e a compensação automática também falhou.",
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "channel": order.channel.value,
                    "region": order.region,
                    "locker_id": order.totem_id,
                },
            )

        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_DEADLINE_REGISTER_FAILED",
                "message": "Pedido revertido automaticamente após falha ao registrar o deadline de pré-pagamento.",
                "order_id": order.id,
                "allocation_id": allocation.id,
                "channel": order.channel.value,
                "region": order.region,
                "locker_id": order.totem_id,
                "compensated": True,
                "local_records_deleted": True,
            },
        )

    return OrderOut(
        order_id=order.id,
        channel=order.channel.value,
        status=order.status.value,
        amount_cents=order.amount_cents,
        payment_method=order.payment_method.value if order.payment_method else None,
        allocation={
            "allocation_id": allocation.id,
            "slot": allocation.slot,
            "ttl_sec": ttl_sec,
        },
    )


@router.get("", response_model=OrderListOut)
def list_orders(
    region: str | None = None,
    status: str | None = None,
    channel: str | None = None,
    scope: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    q = db.query(Order)

    if scope != "ops" and getattr(user, "id", None):
        q = q.filter(Order.user_id == str(user.id))

    if region:
        q = q.filter(Order.region == region)

    if status:
        try:
            status_enum = OrderStatus(status)
            q = q.filter(Order.status == status_enum)
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid status: {status}")

    if channel:
        try:
            channel_enum = OrderChannel(channel)
            q = q.filter(Order.channel == channel_enum)
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid channel: {channel}")

    total = q.count()

    orders = q.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for order in orders:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order.id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )

        pickup = (
            db.query(Pickup)
            .filter(Pickup.order_id == order.id)
            .order_by(Pickup.created_at.desc(), Pickup.id.desc())
            .first()
        )

        normalized_user_id = str(order.user_id) if order.user_id is not None else None

        items.append(
            OrderListItemOut(
                order_id=order.id,
                user_id=normalized_user_id,
                region=order.region,
                channel=order.channel.value,
                status=order.status.value,
                sku_id=order.sku_id,
                totem_id=order.totem_id,
                locker_id=allocation.locker_id if allocation and allocation.locker_id else order.totem_id,
                amount_cents=order.amount_cents,
                payment_method=order.payment_method.value if order.payment_method else None,
                allocation_id=allocation.id if allocation else None,
                slot=allocation.slot if allocation else None,
                allocation_state=allocation.state.value if allocation and allocation.state else None,
                pickup_id=pickup.id if pickup else None,
                pickup_status=pickup.status.value if pickup and pickup.status else None,
                expires_at=pickup.expires_at if pickup else None,
                created_at=order.created_at,
                paid_at=order.paid_at,
                pickup_deadline_at=order.pickup_deadline_at,
                picked_up_at=order.picked_up_at,
            )
        )

    has_prev = page > 1
    has_next = offset + len(items) < total

    return OrderListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )