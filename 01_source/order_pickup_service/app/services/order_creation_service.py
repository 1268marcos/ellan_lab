# 01_source/order_pickup_service/app/services/order_creation_service.py
# 30/03/2026
# coração do sistema
from __future__ import annotations

import logging
import re
import uuid

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
from app.services.locker_service import validate_locker_for_order

LOCKER_ID_PATTERN = re.compile(r"^([A-Z]{2})-[A-Z0-9]+(?:-[A-Z0-9]+)*-LK-\d{3}$")
DEV_LOCKER_ID_PATTERN = re.compile(r"^CACIFO-([A-Z]{2})-\d{3}$")

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
                "region": region,
                "channel": OrderChannel.ONLINE.value,
                "payment_method": payment_method,
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


def validate_locker_id_format(locker_id: str) -> str:
    raw = str(locker_id or "").strip().upper()

    if not raw:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_LOCKER_ID",
                "message": "locker_id não informado.",
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
        },
    )


def _extract_pricing_amount_cents(pricing: dict) -> int:
    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")

    if amount_cents is None:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_RESPONSE",
                "message": "pricing missing amount_cents/price_cents",
            },
        )

    try:
        normalized = int(amount_cents)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_AMOUNT",
                "message": "pricing amount is invalid",
                "amount_cents": amount_cents,
            },
        ) from exc

    if normalized <= 0:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_AMOUNT",
                "message": "pricing amount must be > 0",
                "amount_cents": normalized,
            },
        )

    return normalized


def compensate_failed_online_creation(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
) -> None:
    release_error: Exception | None = None

    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
    except Exception as exc:
        release_error = exc
        logger.exception("online_order_compensation_release_failed")

    try:
        db.delete(allocation)
        db.delete(order)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("online_order_compensation_db_failed")
        raise

    if release_error is not None:
        raise release_error


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
    # =========================
    # 1. VALIDAR LOCKER ID
    # =========================
    totem_id = validate_locker_id_format(totem_id)

    # =========================
    # 2. VALIDAR LOCKER (SOURCE OF TRUTH)
    # =========================
    locker = validate_locker_for_order(
        db=db,
        locker_id=totem_id,
        region=region,
        channel="ONLINE",
        payment_method=payment_method_value,
        card_type=card_type_value,
    )

    # =========================
    # 3. ENUMS
    # =========================
    payment_method = resolve_payment_method_enum(payment_method_value)
    card_type = resolve_card_type_enum(card_type_value)

    # =========================
    # 4. SLOT OBRIGATÓRIO
    # =========================
    if desired_slot is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "DESIRED_SLOT_REQUIRED",
                "message": "desired_slot é obrigatório para pedido ONLINE.",
            },
        )

    try:
        desired_slot = int(desired_slot)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DESIRED_SLOT",
                "message": "desired_slot inválido.",
                "desired_slot": desired_slot,
            },
        ) from exc

    if desired_slot <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DESIRED_SLOT",
                "message": "desired_slot deve ser maior que zero.",
                "desired_slot": desired_slot,
            },
        )

    # =========================
    # 5. TTL (USADO NO BACKEND CENTRAL / LIFECYCLE)
    # =========================
    alloc_ttl_sec = resolve_online_prepayment_ttl_sec(
        region=region,
        payment_method=payment_method.value,
    )

    # =========================
    # 6. PRICING (SOURCE OF TRUTH)
    # =========================
    if amount_cents_input is not None:
        if int(amount_cents_input) <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "INVALID_AMOUNT_CENTS",
                    "message": "amount_cents must be > 0",
                },
            )
        amount_cents = int(amount_cents_input)
    else:
        try:
            pricing = backend_client.get_sku_pricing(
                region,
                sku_id,
                locker_id=totem_id,
            )
        except HTTPError as exc:
            if (
                exc.response is not None
                and exc.response.status_code == 404
                and settings.dev_allow_unknown_sku
            ):
                pricing = {"amount_cents": settings.dev_default_price_cents}
            else:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "type": "PRICING_LOOKUP_FAILED",
                        "message": "Falha ao consultar pricing do SKU.",
                        "sku_id": sku_id,
                        "locker_id": totem_id,
                        "region": region,
                    },
                ) from exc

        amount_cents = _extract_pricing_amount_cents(pricing)

    # =========================
    # 7. ALLOCATION NO RUNTIME (EXECUÇÃO PURA)
    # =========================
    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            region=region,
            sku_id=sku_id,
            ttl_sec=alloc_ttl_sec,
            request_id=request_id,
            desired_slot=desired_slot,
            locker_id=totem_id,
        )
    except HTTPError as exc:
        runtime_detail = None
        status_code = 502

        if exc.response is not None:
            status_code = 409 if exc.response.status_code == 409 else 502
            try:
                runtime_detail = exc.response.json()
            except Exception:
                runtime_detail = exc.response.text

        raise HTTPException(
            status_code=status_code,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao executar reserva do slot no runtime.",
                "locker_id": totem_id,
                "region": region,
                "desired_slot": desired_slot,
                "request_id": request_id,
                "runtime_detail": runtime_detail,
            },
        ) from exc

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    runtime_state = alloc.get("state")

    if not allocation_id or slot is None:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "INVALID_ALLOCATION_RESPONSE",
                "message": "Resposta inválida do runtime para allocation.",
                "runtime_response": alloc,
            },
        )

    try:
        slot = int(slot)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "INVALID_ALLOCATION_RESPONSE",
                "message": "slot retornado pelo runtime é inválido.",
                "runtime_response": alloc,
            },
        ) from exc

    # defesa extra: runtime executor não pode trocar o slot decidido
    if slot != desired_slot:
        try:
            backend_client.locker_release(
                region,
                allocation_id,
                locker_id=totem_id,
            )
        except Exception:
            logger.exception("allocation_slot_mismatch_release_failed")

        raise HTTPException(
            status_code=502,
            detail={
                "type": "ALLOCATION_SLOT_MISMATCH",
                "message": "Runtime retornou slot diferente do slot decidido pelo backend central.",
                "desired_slot": desired_slot,
                "runtime_slot": slot,
                "locker_id": totem_id,
                "allocation_id": allocation_id,
                "runtime_state": runtime_state,
            },
        )

    # =========================
    # 8. ORDER
    # =========================
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

    try:
        db.add(order)
        db.flush()

        allocation = Allocation(
            id=allocation_id,
            order_id=order.id,
            locker_id=totem_id,
            slot=slot,
            state=AllocationState.RESERVED_PENDING_PAYMENT,
        )

        db.add(allocation)
        db.commit()
        db.refresh(order)
        db.refresh(allocation)
    except Exception as exc:
        db.rollback()

        try:
            backend_client.locker_release(
                region,
                allocation_id,
                locker_id=totem_id,
            )
        except Exception:
            logger.exception("online_order_db_failure_release_failed")

        raise HTTPException(
            status_code=500,
            detail={
                "type": "ORDER_PERSISTENCE_FAILED",
                "message": "Falha ao persistir pedido/alocação após reserva no runtime.",
                "order_id": order.id,
                "allocation_id": allocation_id,
                "locker_id": totem_id,
                "slot": slot,
            },
        ) from exc

    # =========================
    # 9. LIFECYCLE
    # =========================
    try:
        register_prepayment_timeout_deadline(
            order_id=order.id,
            order_channel=order.channel.value,
            region_code=order.region,
            slot_id=str(allocation.slot),
            machine_id=order.totem_id,
            created_at=order.created_at,
            payment_method=order.payment_method.value,
        )
    except LifecycleClientError:
        compensate_failed_online_creation(
            db=db,
            order=order,
            allocation=allocation,
        )
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_REGISTER_FAILED",
                "message": "Falha ao registrar deadline no lifecycle.",
                "order_id": order.id,
                "allocation_id": allocation.id,
                "locker_id": order.totem_id,
            },
        )

    return CreateOrderCoreResult(
        order=order,
        allocation=allocation,
        ttl_sec=alloc_ttl_sec,
    )