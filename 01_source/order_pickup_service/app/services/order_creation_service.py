# 01_source/order_pickup_service/app/services/order_creation_service.py
from __future__ import annotations

import logging
import uuid
import re

from dataclasses import dataclass

from fastapi import HTTPException
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.lifecycle_client import LifecycleClientError
from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds
from app.models.allocation import Allocation, AllocationState
from app.models.order import CardType, Order, OrderChannel, OrderStatus, PaymentMethod
from app.services import backend_client
from app.services.lifecycle_integration import register_prepayment_timeout_deadline

LOCKER_ID_PATTERN = re.compile(r"^(SP|PT)-[A-Z0-9]+(?:-[A-Z0-9]+)*-LK-\d{3}$")
DEV_LOCKER_ID_PATTERN = re.compile(r"^CACIFO-(SP|PT)-\d{3}$")

logger = logging.getLogger(__name__)



@dataclass
class CreateOrderCoreResult:
    order: Order
    allocation: Allocation
    ttl_sec: int


def normalize_upper_list(values: list[str] | None) -> list[str]:
    return [str(v).strip().upper() for v in (values or []) if str(v).strip()]


def resolve_online_prepayment_ttl_sec(*, region: str, payment_method: str) -> int:
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


def resolve_payment_method_enum(method_value: str) -> PaymentMethod:
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


def resolve_card_type_enum(card_type_value: str | None) -> CardType | None:
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


def validate_online_locker_context(*, region: str, totem_id: str, payment_method: str) -> dict:
    locker = backend_client.get_locker_registry_item(totem_id)

    if not locker:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {totem_id}",
                "locker_id": totem_id,
                "retryable": False,
            },
        )

    if not bool(locker.get("active", False)):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_INACTIVE",
                "message": "O locker informado está inativo.",
                "locker_id": totem_id,
                "retryable": False,
            },
        )

    locker_region = str(locker.get("region") or "").strip().upper()
    payload_region = str(region or "").strip().upper()

    if locker_region != payload_region:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_REGION_MISMATCH",
                "message": "O locker informado não pertence à região do pedido.",
                "locker_id": totem_id,
                "payload_region": payload_region,
                "locker_region": locker_region,
                "retryable": False,
            },
        )

    channels = normalize_upper_list(locker.get("channels"))
    if "ONLINE" not in channels:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": "O locker informado não aceita pedidos no canal ONLINE.",
                "locker_id": totem_id,
                "allowed_channels": channels,
                "retryable": False,
            },
        )

    payment_methods = normalize_upper_list(locker.get("payment_methods"))
    requested_method = str(payment_method or "").strip().upper()

    if requested_method not in payment_methods:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_PAYMENT_METHOD_NOT_ALLOWED",
                "message": "O método de pagamento informado não é permitido para este locker.",
                "locker_id": totem_id,
                "payment_method": requested_method,
                "allowed_payment_methods": payment_methods,
                "retryable": False,
            },
        )

    return locker


def compensate_failed_online_creation(
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


def validate_locker_id_format(locker_id: str) -> str:
    raw = str(locker_id or "").strip().upper()

    if not raw:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_LOCKER_ID",
                "message": "locker_id não informado.",
                "locker_id": locker_id,
                "retryable": False,
            },
        )

    if LOCKER_ID_PATTERN.match(raw):
        return raw

    if DEV_LOCKER_ID_PATTERN.match(raw):
        return raw

    raise HTTPException(
        status_code=400,
        detail={
            "type": "INVALID_LOCKER_ID_FORMAT",
            "message": f"Formato inválido de locker_id: {raw}",
            "locker_id": raw,
            "retryable": False,
        },
    )


def create_order_core(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    payment_method_value: str,
    card_type_value: str | None,
    amount_cents_input: int | None,
    guest_phone: str | None,
    user_id: str | None,
) -> CreateOrderCoreResult:

    totem_id = validate_locker_id_format(totem_id)

    validate_online_locker_context(
        region=region,
        totem_id=totem_id,
        payment_method=payment_method_value,
    )

    payment_method = resolve_payment_method_enum(payment_method_value)
    card_type = resolve_card_type_enum(card_type_value)

    alloc_ttl_sec = resolve_online_prepayment_ttl_sec(
        region=region,
        payment_method=payment_method.value,
    )

    amount_cents = None

    if amount_cents_input is not None:
        if int(amount_cents_input) <= 0:
            raise HTTPException(status_code=400, detail="amount_cents must be > 0")
        amount_cents = int(amount_cents_input)

    if amount_cents is None:
        try:
            pricing = backend_client.get_sku_pricing(
                region,
                sku_id,
                locker_id=totem_id,
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
            region,
            sku_id,
            alloc_ttl_sec,
            request_id,
            desired_slot,
            locker_id=totem_id,
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
                    "desired_slot": desired_slot,
                    "region": region,
                    "locker_id": totem_id,
                    "backend_detail": backend_detail,
                },
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao alocar gaveta no backend.",
                "region": region,
                "locker_id": totem_id,
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", alloc_ttl_sec))

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
        payment_method=payment_method,
        card_type=card_type,
        guest_phone=guest_phone,
    )
    db.add(order)
    db.flush()

    allocation = Allocation(
        id=allocation_id,
        order_id=order.id,
        locker_id=totem_id,
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
            compensate_failed_online_creation(
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

    return CreateOrderCoreResult(
        order=order,
        allocation=allocation,
        ttl_sec=ttl_sec,
    )