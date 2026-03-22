# 01_source/order_pickup_service/app/routers/kiosk.py
# Aqui faz pedido KIOSK
# Router: /kiosk/orders

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds
from app.models.allocation import Allocation, AllocationState
from app.models.order import (
    CardType,
    Order,
    OrderChannel,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.models.pickup import (
    Pickup,
    PickupChannel,
    PickupLifecycleStage,
    PickupStatus,
)
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

from app.services.payment_confirm_service import confirm_payment_and_emit_event

router = APIRouter(prefix="/kiosk", tags=["kiosk"])
logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_allocation_by_order(db: Session, order_id: str) -> Allocation | None:
    return db.query(Allocation).filter(Allocation.order_id == order_id).first()


def _resolve_payment_method_enum(method_value: str) -> PaymentMethod:
    try:
        return PaymentMethod(method_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_PAYMENT_METHOD",
                "message": f"Método de pagamento não suportado no pedido KIOSK: {method_value}",
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


def _resolve_kiosk_alloc_ttl_sec(*, region: str, payment_method: str) -> int:
    ttl_sec = resolve_prepayment_timeout_seconds(
        region_code=region,
        order_channel=OrderChannel.KIOSK.value,
        payment_method=payment_method,
    )

    if int(ttl_sec) <= 0:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "KIOSK_PAYMENT_TTL_POLICY_INVALID",
                "message": "O TTL configurado deve ser maior que zero.",
                "region": str(region or "").strip().upper(),
                "channel": OrderChannel.KIOSK.value,
                "payment_method": str(payment_method or "").strip().upper(),
                "ttl_value": ttl_sec,
            },
        )

    return int(ttl_sec)


def _build_kiosk_payment_preview(
    *,
    payment_method: PaymentMethod,
    card_type: CardType | None,
    customer_phone: str | None,
    ttl_sec: int,
    amount_cents: int,
    region: str,
) -> tuple[PaymentStatus, str | None, Dict[str, Any]]:
    expires_at_epoch = int(datetime.now(timezone.utc).timestamp()) + int(ttl_sec)

    if payment_method == PaymentMethod.PIX:
        return (
            PaymentStatus.PENDING_CUSTOMER_ACTION,
            "DISPLAY_QR",
            {
                "instruction": "O pagamento PIX deverá apresentar QRCode no passo seguinte do fluxo.",
                "expires_in_sec": int(ttl_sec),
                "expires_at_epoch": expires_at_epoch,
                "region": region,
            },
        )

    if payment_method == PaymentMethod.CARTAO:
        return (
            PaymentStatus.PENDING_CUSTOMER_ACTION,
            "MANUAL_CARD_ENTRY",
            {
                "instruction": "O cliente deverá digitar os dados do cartão no painel do KIOSK.",
                "card_type": card_type.value if card_type else None,
                "expires_in_sec": int(ttl_sec),
                "expires_at_epoch": expires_at_epoch,
            },
        )

    if payment_method == PaymentMethod.MBWAY:
        return (
            PaymentStatus.PENDING_PROVIDER_CONFIRMATION,
            "PHONE_APPROVAL",
            {
                "instruction": "O cliente deverá autorizar o pagamento na aplicação MB WAY.",
                "customer_phone": customer_phone,
                "expires_in_sec": int(ttl_sec),
                "expires_at_epoch": expires_at_epoch,
            },
        )

    if payment_method == PaymentMethod.MULTIBANCO_REFERENCE:
        return (
            PaymentStatus.PENDING_CUSTOMER_ACTION,
            "DISPLAY_REFERENCE",
            {
                "instruction": "A referência Multibanco será gerada no passo seguinte do fluxo.",
                "expires_in_sec": int(ttl_sec),
                "expires_at_epoch": expires_at_epoch,
                "amount_cents": amount_cents,
            },
        )

    if payment_method in {
        PaymentMethod.NFC,
        PaymentMethod.APPLE_PAY,
        PaymentMethod.GOOGLE_PAY,
        PaymentMethod.MERCADO_PAGO_WALLET,
    }:
        return (
            PaymentStatus.AWAITING_INTEGRATION,
            "AWAITING_INTEGRATION",
            {
                "instruction": f"O método {payment_method.value} está preparado, mas ainda depende de integração completa.",
                "expires_in_sec": int(ttl_sec),
                "expires_at_epoch": expires_at_epoch,
            },
        )

    return (
        PaymentStatus.CREATED,
        None,
        {},
    )


def _normalize_upper_list(values: list[str] | None) -> list[str]:
    return [str(v).strip().upper() for v in (values or []) if str(v).strip()]


def _validate_kiosk_locker_context(payload: KioskOrderCreateIn) -> dict:
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
    if "KIOSK" not in channels:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": "O locker informado não aceita pedidos no canal KIOSK.",
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


def _compensate_failed_kiosk_creation(
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
            "kiosk_order_compensation_release_failed",
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
            "kiosk_order_compensation_db_failed",
            extra={
                "order_id": order.id,
                "allocation_id": allocation.id,
            },
        )
        raise


def _ensure_kiosk_pickup(
    db: Session,
    *,
    order: Order,
    allocation: Allocation,
) -> Pickup:
    now = _utc_now_naive()

    existing_pickup = (
        db.query(Pickup)
        .filter(
            Pickup.order_id == order.id,
            Pickup.status == PickupStatus.ACTIVE,
        )
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )

    if existing_pickup:
        pickup = existing_pickup
        pickup.channel = PickupChannel.KIOSK
        pickup.region = order.region
        pickup.locker_id = allocation.locker_id or order.totem_id
        pickup.machine_id = order.totem_id
        pickup.slot = str(allocation.slot) if allocation.slot is not None else None
        pickup.operator_id = pickup.operator_id
        pickup.tenant_id = pickup.tenant_id
        pickup.site_id = pickup.site_id
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.DOOR_OPENED
        pickup.current_token_id = None
        pickup.activated_at = pickup.activated_at or now
        pickup.ready_at = pickup.ready_at or now
        pickup.expires_at = None
        pickup.door_opened_at = pickup.door_opened_at or now
        pickup.item_removed_at = None
        pickup.door_closed_at = None
        pickup.redeemed_at = None
        pickup.redeemed_via = None
        pickup.expired_at = None
        pickup.cancelled_at = None
        pickup.cancel_reason = None
        pickup.notes = "Pickup liberado via fluxo KIOSK."
        pickup.updated_at = now
        return pickup

    pickup = Pickup(
        id=str(uuid.uuid4()),
        order_id=order.id,
        channel=PickupChannel.KIOSK,
        region=order.region,
        locker_id=allocation.locker_id or order.totem_id,
        machine_id=order.totem_id,
        slot=str(allocation.slot) if allocation.slot is not None else None,
        operator_id=None,
        tenant_id=None,
        site_id=None,
        status=PickupStatus.ACTIVE,
        lifecycle_stage=PickupLifecycleStage.DOOR_OPENED,
        current_token_id=None,
        activated_at=now,
        ready_at=now,
        expires_at=None,
        door_opened_at=now,
        item_removed_at=None,
        door_closed_at=None,
        redeemed_at=None,
        redeemed_via=None,
        expired_at=None,
        cancelled_at=None,
        cancel_reason=None,
        correlation_id=None,
        source_event_id=None,
        sensor_event_id=None,
        notes="Pickup liberado via fluxo KIOSK.",
        created_at=now,
        updated_at=now,
    )
    db.add(pickup)
    db.flush()
    return pickup


@router.post("/orders", response_model=KioskOrderOut)
def kiosk_create_order(
    payload: KioskOrderCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    x_device_fingerprint: str | None = Header(default=None, alias="X-Device-Fingerprint"),
):
    _validate_kiosk_locker_context(payload)

    check_kiosk_antifraud(
        db=db,
        request=request,
        totem_id=payload.totem_id,
        region=payload.region.value,
        device_fingerprint=x_device_fingerprint,
    )

    payment_method = _resolve_payment_method_enum(payload.payment_method.value)
    card_type = _resolve_card_type_enum(
        payload.card_type.value if payload.card_type else None
    )

    alloc_ttl_sec = _resolve_kiosk_alloc_ttl_sec(
        region=payload.region.value,
        payment_method=payment_method.value,
    )

    pricing = backend_client.get_sku_pricing(
        payload.region.value,
        payload.sku_id,
        locker_id=payload.totem_id,
    )
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
                    "message": "A gaveta escolhida não está disponível no momento.",
                    "desired_slot": payload.desired_slot,
                    "sku_id": payload.sku_id,
                    "region": payload.region.value,
                    "locker_id": payload.totem_id,
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

    payment_status, instruction_type, payment_payload = _build_kiosk_payment_preview(
        payment_method=payment_method,
        card_type=card_type,
        customer_phone=payload.customer_phone.strip() if payload.customer_phone else None,
        ttl_sec=ttl_sec,
        amount_cents=int(amount_cents),
        region=payload.region.value,
    )

    order = Order(
        id=str(uuid.uuid4()),
        user_id=None,
        channel=OrderChannel.KIOSK,
        region=payload.region.value,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        payment_method=payment_method,
        payment_status=payment_status,
        card_type=card_type,
        guest_phone=payload.customer_phone.strip() if payload.customer_phone else None,
        guest_email=None,
        pickup_deadline_at=None,
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
            _compensate_failed_kiosk_creation(
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

    return KioskOrderOut(
        order_id=order.id,
        status=order.status.value,
        slot=allocation.slot,
        amount_cents=order.amount_cents,
        payment_method=order.payment_method.value if order.payment_method else "",
        allocation_id=allocation.id,
        ttl_sec=ttl_sec,
        message=f"Reserva criada. Conclua o pagamento para liberar a gaveta {allocation.slot}.",
        payment_status=order.payment_status.value if order.payment_status else None,
        payment_instruction_type=instruction_type,
        payment_payload=payment_payload,
    )


@router.post("/orders/{order_id}/payment-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.channel == OrderChannel.KIOSK)
        .first()
    )
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
            payment_method=order.payment_method.value if order.payment_method else None,
            message="Pagamento já aprovado anteriormente.",
        )

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    try:
        backend_client.locker_commit(
            order.region,
            allocation.id,
            locked_until_iso=None,
            locker_id=order.totem_id,
        )
        backend_client.locker_light_on(
            order.region,
            allocation.slot,
            locker_id=order.totem_id,
        )
        backend_client.locker_open(
            order.region,
            allocation.slot,
            locker_id=order.totem_id,
        )
        backend_client.locker_set_state(
            order.region,
            allocation.slot,
            "OUT_OF_STOCK",
            locker_id=order.totem_id,
        )
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
                "locker_id": order.totem_id,
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
                "locker_id": order.totem_id,
                "error": str(e),
            },
        )

    order.paid_at = _utc_now_naive()
    order.status = OrderStatus.DISPENSED
    order.mark_payment_approved()

    # 🔥 GARANTIR transaction_id
    order.gateway_transaction_id = order.gateway_transaction_id or f"kiosk-{order.id}"

    allocation.state = AllocationState.OPENED_FOR_PICKUP
    allocation.locked_until = None

    pickup = _ensure_kiosk_pickup(
        db,
        order=order,
        allocation=allocation,
    )

    # 🔥 EVENTO FINANCEIRO
    confirm_payment_and_emit_event(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        amount_cents=order.amount_cents,
        currency="BRL",
        source="kiosk",
    )

    db.commit()
    db.refresh(order)
    db.refresh(allocation)
    db.refresh(pickup)

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
        payment_method=order.payment_method.value if order.payment_method else None,
        message=f"Pagamento aprovado. Retire o produto na gaveta {allocation.slot}.",
    )


@router.post("/identify", response_model=KioskIdentifyOut)
def kiosk_identify_customer(
    payload: KioskCustomerIdentifyIn,
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == payload.order_id, Order.channel == OrderChannel.KIOSK)
        .first()
    )
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