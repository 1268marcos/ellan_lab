# 01_source/order_pickup_service/app/services/order_creation_service.py
#
# ESSA É FOI UMA ENTREGA ONDE QUESTIONEI A QUALIDADE
# 
# PROVAVEL ERRO
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

# Padrão mais flexível que aceita qualquer código de região de 2 caracteres (maiúsculas)
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
    """
    Valida o formato do locker_id.

    Formatos aceitos:
    - Produção: {REGIAO}-{LOCALIDADE}-{SUFIXO}-LK-{NUMERO}
      Ex: PT-MAIA-CENTRO-LK-001, SP-CARAPICUIBA-JDMARILU-LK-002
    - Desenvolvimento: CACIFO-{REGIAO}-{NUMERO}
      Ex: CACIFO-PT-001, CACIFO-SP-001
    """
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
            "message": (
                f"Formato inválido de locker_id: {raw}. "
                f"Formato esperado: {{REGIAO}}-{{LOCAL}}-{{SUFIXO}}-LK-{{NUMERO}} "
                f"(ex: PT-MAIA-CENTRO-LK-001) "
                f"ou CACIFO-{{REGIAO}}-{{NUMERO}} para desenvolvimento."
            ),
            "locker_id": raw,
            "retryable": False,
        },
    )


def _extract_product_context_from_pricing(
    *,
    pricing: dict | None,
    amount_cents_input: int | None,
) -> tuple[int, str | None, float | None]:
    """
    Deriva contexto mínimo do produto a partir do payload de pricing/SKU.

    Retorna:
    - amount_cents_final
    - product_category (se disponível)
    - product_value em unidade monetária (ex.: 48.50)
    """
    pricing = pricing or {}

    resolved_amount_cents = amount_cents_input
    if resolved_amount_cents is not None:
        if int(resolved_amount_cents) <= 0:
            raise HTTPException(status_code=400, detail="amount_cents must be > 0")
        resolved_amount_cents = int(resolved_amount_cents)
    else:
        resolved_amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")

    if resolved_amount_cents is None:
        raise HTTPException(
            status_code=502,
            detail="pricing missing amount_cents/price_cents from backend",
        )

    product_category = (
        pricing.get("category")
        or pricing.get("product_category")
        or pricing.get("category_id")
    )
    if product_category is not None:
        product_category = str(product_category).strip().upper() or None

    product_value = None
    try:
        product_value = int(resolved_amount_cents) / 100.0
    except Exception:
        product_value = None

    return int(resolved_amount_cents), product_category, product_value


def _load_pricing_for_online_order(
    *,
    region: str,
    sku_id: str,
    totem_id: str,
) -> dict:
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

    if not isinstance(pricing, dict):
        raise HTTPException(
            status_code=502,
            detail="invalid pricing payload from backend",
        )

    return pricing


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
    """
    Criação de pedido ONLINE com validação completa de locker e produto.
    """

    region = str(region or "").strip().upper()
    sku_id = str(sku_id or "").strip()
    totem_id = validate_locker_id_format(totem_id)

    if not region:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_REGION",
                "message": "region não informada.",
                "retryable": False,
            },
        )

    if not sku_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_SKU_ID",
                "message": "sku_id não informado.",
                "retryable": False,
            },
        )

    if int(desired_slot) <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DESIRED_SLOT",
                "message": "desired_slot deve ser maior que zero.",
                "desired_slot": desired_slot,
                "retryable": False,
            },
        )

    payment_method = resolve_payment_method_enum(payment_method_value)
    card_type = resolve_card_type_enum(card_type_value)

    pricing = _load_pricing_for_online_order(
        region=region,
        sku_id=sku_id,
        totem_id=totem_id,
    )

    amount_cents, product_category, product_value = _extract_product_context_from_pricing(
        pricing=pricing,
        amount_cents_input=amount_cents_input,
    )

    # SOURCE OF TRUTH = locker persistido no banco
    # Só valida compatibilidade de produto se a categoria vier do backend.
    locker = validate_locker_for_order(
        db=db,
        locker_id=totem_id,
        region=region,
        channel=OrderChannel.ONLINE.value,
        payment_method=payment_method.value,
        product_category=product_category,
        product_value=product_value,
        product_weight_kg=None,
        product_dimensions=None,
    )

    alloc_ttl_sec = resolve_online_prepayment_ttl_sec(
        region=region,
        payment_method=payment_method.value,
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
        raise HTTPException(
            status_code=502,
            detail="locker allocate missing allocation_id/slot",
        )

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
        # Campos adicionais de locker/produto só devem entrar aqui
        # quando existirem de fato no model e na migration.
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

    logger.info(
        "online_order_created",
        extra={
            "order_id": order.id,
            "allocation_id": allocation.id,
            "region": order.region,
            "locker_id": order.totem_id,
            "slot": allocation.slot,
            "sku_id": order.sku_id,
            "amount_cents": order.amount_cents,
            "payment_method": order.payment_method.value if order.payment_method else None,
            "product_category": product_category,
            "locker_db_id": getattr(locker, "id", None),
        },
    )

    return CreateOrderCoreResult(
        order=order,
        allocation=allocation,
        ttl_sec=ttl_sec,
    )