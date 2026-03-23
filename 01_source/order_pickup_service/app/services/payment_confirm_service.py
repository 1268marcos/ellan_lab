# 01_source/order_pickup_service/app/services/payment_confirm_service.py
from __future__ import annotations

import hashlib
import logging
import uuid

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.domain_event_outbox import DomainEventOutbox
from app.models.order import Order
from app.services.domain_event_outbox_service import enqueue_order_paid_event

from app.models.fiscal_document import FiscalDocument

logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _enum_value_or_raw(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _build_fiscal_receipt_code(*, order: Order) -> str:
    channel = _enum_value_or_raw(order.channel) or "UNK"
    digest = hashlib.sha256(f"{channel}:{order.id}".encode("utf-8")).hexdigest()[:12].upper()
    prefix = "KSK" if channel == "KIOSK" else "ONL"
    return f"{prefix}-{digest}"


def _build_fiscal_simulation_payload(
    *,
    order: Order,
    currency: str,
) -> dict[str, Any]:
    receipt_code = _build_fiscal_receipt_code(order=order)

    send_target = (
        getattr(order, "receipt_email", None)
        or getattr(order, "guest_email", None)
        or getattr(order, "receipt_phone", None)
        or getattr(order, "guest_phone", None)
    )

    channel = _enum_value_or_raw(order.channel)
    region = str(getattr(order, "region", "") or "").strip().upper()

    document_type = "NFE" if region == "SP" else "FISCAL_RECEIPT_SIMULATED"
    delivery_mode = "PRINT" if channel == "KIOSK" else "SEND"

    return {
        "mode": "SIMULATED",
        "requested": True,
        "document_type": document_type,
        "currency": str(currency or "").strip().upper(),
        "purchase_reference": order.id,
        "receipt_code": receipt_code,
        "delivery_mode": delivery_mode,
        "send_status": (
            "SIMULATED_QUEUED"
            if (delivery_mode == "SEND" and send_target)
            else "SIMULATED_NOT_REQUESTED"
        ),
        "send_target": send_target,
        "print_status": (
            "SIMULATED_AVAILABLE"
            if delivery_mode == "PRINT"
            else "SIMULATED_NOT_APPLICABLE"
        ),
        "print_site_path": f"/public/fiscal/print/{receipt_code}",
        "print_label": "Use este código no site de impressão do comprovante/cupom simulado.",
    }


def apply_payment_confirmation(
    *,
    db: Session,
    order: Order,
    transaction_id: str | None,
    payment_method,
    amount_cents: int | None,
    currency: str | None,
    source: str,
) -> None:
    """
    Consolida a parte financeira da confirmação de pagamento:
    - validações financeiras
    - fallback de gateway_transaction_id
    - marcação de paid_at / payment approved

    Não decide fluxo ONLINE/KIOSK.
    Não decide status operacional do pedido.
    """

    if order is None:
        raise ValueError("order obrigatório")

    if not order.amount_cents or int(order.amount_cents) <= 0:
        raise ValueError("amount_cents do pedido inválido")

    if amount_cents is None or int(amount_cents) <= 0:
        raise ValueError("amount_cents informado inválido")

    if int(amount_cents) != int(order.amount_cents):
        raise ValueError(
            f"amount mismatch: order={order.amount_cents} payload={amount_cents}"
        )

    if not currency or not str(currency).strip():
        raise ValueError("currency obrigatória")

    if payment_method:
        order.payment_method = payment_method

    if transaction_id and str(transaction_id).strip():
        order.gateway_transaction_id = str(transaction_id).strip()

    if not order.gateway_transaction_id:
        order.gateway_transaction_id = f"{source}-{order.id}"

    if not getattr(order, "paid_at", None):
        order.paid_at = _utc_now_naive()

    order.mark_payment_approved()

    logger.info(
        "payment_confirmation_applied",
        extra={
            "order_id": order.id,
            "source": source,
            "payment_method": _enum_value_or_raw(order.payment_method),
            "transaction_id": order.gateway_transaction_id,
            "amount_cents": order.amount_cents,
            "currency": str(currency).strip().upper(),
        },
    )


def emit_order_paid_and_simulate_fiscal(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup,
    currency: str,
    source: str,
) -> dict[str, Any]:
    """
    Consolida:
    - idempotência por outbox
    - emissão de order.paid
    - simulação de geração/envio/impressão fiscal

    A emissão oficial continua sendo downstream, a partir de order.paid.
    """

    if order is None:
        raise ValueError("order obrigatório")

    if allocation is None:
        raise ValueError("allocation obrigatório")

    if not currency or not str(currency).strip():
        raise ValueError("currency obrigatória")

    event_key = f"order.paid:{order.id}"

    existing = (
        db.query(DomainEventOutbox)
        .filter(DomainEventOutbox.event_key == event_key)
        .first()
    )

    event_already_exists = existing is not None

    if not existing:
        enqueue_order_paid_event(
            db,
            order_id=order.id,
            region=order.region,
            channel=_enum_value_or_raw(order.channel),
            payment_method=_enum_value_or_raw(order.payment_method),
            transaction_id=order.gateway_transaction_id,
            amount_cents=order.amount_cents,
            currency=str(currency).strip().upper(),
            locker_id=(pickup.locker_id if pickup else order.totem_id),
            machine_id=(pickup.machine_id if pickup else order.totem_id),
            slot=(pickup.slot if pickup else allocation.slot),
            allocation_id=allocation.id,
            pickup_id=(pickup.id if pickup else None),
            tenant_id=None,
            operator_id=None,
            site_id=None,
            source_service="order_pickup_service",
        )

        logger.info(
            "payment_confirm_event_enqueued",
            extra={
                "order_id": order.id,
                "event_key": event_key,
                "source": source,
                "channel": _enum_value_or_raw(order.channel),
                "amount_cents": order.amount_cents,
            },
        )
    else:
        logger.info(
            "payment_confirm_event_already_exists",
            extra={
                "order_id": order.id,
                "event_key": event_key,
                "event_status": existing.status,
                "source": source,
            },
        )

    currency_norm = str(currency).strip().upper()

    existing_fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )

    if existing_fiscal:
        fiscal = existing_fiscal.payload_json
    else:
        fiscal = _build_fiscal_simulation_payload(
            order=order,
            currency=currency_norm,
        )

        fiscal_doc = FiscalDocument(
            id=str(uuid.uuid4()),
            order_id=order.id,
            receipt_code=fiscal["receipt_code"],
            document_type=fiscal["document_type"],
            channel=_enum_value_or_raw(order.channel),
            region=order.region,
            amount_cents=order.amount_cents,
            currency=currency_norm,
            delivery_mode=fiscal["delivery_mode"],
            send_status=fiscal["send_status"],
            send_target=fiscal.get("send_target"),
            print_status=fiscal["print_status"],
            print_site_path=fiscal["print_site_path"],
            payload_json=fiscal,
            issued_at=_utc_now_naive(),
        )

        db.add(fiscal_doc)

        logger.info(
            "fiscal_document_persisted",
            extra={
                "order_id": order.id,
                "receipt_code": fiscal["receipt_code"],
                "channel": _enum_value_or_raw(order.channel),
            },
        )

    logger.info(
        "payment_confirm_fiscal_simulated",
        extra={
            "order_id": order.id,
            "receipt_code": fiscal["receipt_code"],
            "delivery_mode": fiscal["delivery_mode"],
            "source": source,
        },
    )

    return {
        "event_key": event_key,
        "event_already_exists": event_already_exists,
        "fiscal": fiscal,
    }


def confirm_payment_and_emit_event(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup,
    amount_cents: int | None,
    currency: str | None,
    source: str,
) -> dict[str, Any]:
    """
    Compatibilidade retroativa com o service já existente.
    Mantém o nome antigo para não quebrar chamadas atuais, mas agora
    delega para as funções mais explícitas.
    """

    apply_payment_confirmation(
        db=db,
        order=order,
        transaction_id=getattr(order, "gateway_transaction_id", None),
        payment_method=getattr(order, "payment_method", None),
        amount_cents=amount_cents,
        currency=currency,
        source=source,
    )

    return emit_order_paid_and_simulate_fiscal(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        currency=str(currency or "").strip().upper(),
        source=source,
    )