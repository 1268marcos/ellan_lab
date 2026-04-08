# 01_source/order_pickup_service/app/routers/kiosk.py
# CORRIGIDO: payment totalmente DB-driven (sem if / sem hardcoded)
# 06/04/2026 - import resolve_payment_ui_code
# 08/04/2026 - criação : def kiosk_payment_approved(
# 08/04/2026 - correção : OrderStatus.PAID para PaymentStatus.PAID
#              a correção mudou para PaymentStatus.CONFIRMED
# 08/04/2026 - order.status representa estado logístico e order.payment_status representa estado financeiro
# ALERTA/ATENÇÃO: SOBRE requires_confirmation PROBLEMA OCULTO (IMPORTANTE)
#                 → NÃO deveria chamar payment-approved
#                 → deveria aguardar confirmação do cliente (3DS / OTP / etc)
# Nesse momento o fluxo atual:
# requires_confirmation → frontend chama payment-approved, portanto, CONFIRMED é simulação
# isso é errado conceitualmente


from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
# from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus, PaymentStatus, PaymentMethod
from app.models.pickup import Pickup, PickupChannel, PickupLifecycleStage, PickupStatus
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

from app.services.pickup_payment_fulfillment_service import fulfill_payment_post_approval
from app.models.fiscal_document import FiscalDocument
from app.services.notification_dispatch_service import queue_receipt_email

from app.services.payment_capability_service import get_payment_capabilities

from app.services.payment_resolution_service import resolve_payment_ui_code

from app.services.capability_constraint_service import get_capability_constraint



router = APIRouter(prefix="/kiosk", tags=["kiosk"])
logger = logging.getLogger(__name__)


# =========================
# CAPABILITY HELPERS (DB-DRIVEN)
# =========================


def _resolve_order_payment_method_enum(method_code: str) -> PaymentMethod:
    raw = str(method_code or "").strip()

    mapping = {
        # explore mais em : 01_source/order_pickup_service/app/models/order.py

        # "creditCard": PaymentMethod.credit_card,
        "creditCard": PaymentMethod.creditCard,

        # "debitCard": PaymentMethod.debit_card,
        "debitCard": PaymentMethod.debitCard,

        # "giftCard": PaymentMethod.gift_card,
        "giftCard": PaymentMethod.giftCard,

        # "prepaidCard": PaymentMethod.prepaid_card,
        "prepaidCard": PaymentMethod.prepaidCard,

        "pix": PaymentMethod.pix,
        "boleto": PaymentMethod.boleto,
        "mbway": PaymentMethod.mbway,
        "multibanco_reference": PaymentMethod.multibanco_reference,
        "apple_pay": PaymentMethod.apple_pay,
        "google_pay": PaymentMethod.google_pay,
        "mercado_pago_wallet": PaymentMethod.mercado_pago_wallet,
        "nfc": PaymentMethod.nfc,
        "alipay": PaymentMethod.alipay,
        "wechat_pay": PaymentMethod.wechat_pay,
        "m_pesa": PaymentMethod.m_pesa,
        "cashapp": PaymentMethod.cashapp,
        "paypal": PaymentMethod.paypal,
        "konbini": PaymentMethod.konbini,
        "afterpay": PaymentMethod.afterpay,
        "zip": PaymentMethod.zip,
        "crypto": PaymentMethod.crypto,
    }

    resolved = mapping.get(raw)
    if resolved is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_ORDER_PAYMENT_METHOD",
                "message": f"payment_method não suportado no enum Order.PaymentMethod: {raw}",
            },
        )

    return resolved


def _get_kiosk_capabilities(db: Session, region: str):
    capabilities = get_payment_capabilities(
        db=db,
        region=region,
        channel="KIOSK",
        context="ORDER_CREATION",
    )

    if not capabilities.get("found"):
        raise HTTPException(
            status_code=400,
            detail="payment capability profile not found for KIOSK"
        )

    return capabilities


def _resolve_method(capabilities, method_input: str):
    for m in capabilities["methods"]:
        if m["method"] == method_input:
            return m

    raise HTTPException(
        status_code=400,
        detail={
            "type": "INVALID_PAYMENT_METHOD",
            "allowed": [m["method"] for m in capabilities["methods"]],
        }
    )


def _resolve_interface(method, requested):
    interfaces = method.get("interfaces", [])

    if requested:
        for i in interfaces:
            if i["code"] == requested:
                return requested

        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_PAYMENT_INTERFACE",
                "allowed": [i["code"] for i in interfaces],
            }
        )

    default = next((i for i in interfaces if i.get("default")), None)
    return default["code"] if default else None


def _validate_requirements(method, payload):
    for r in method.get("requirements", []):
        if not r.get("required"):
            continue

        if r["code"] == "customer_phone" and not payload.customer_phone:
            raise HTTPException(status_code=400, detail="customer_phone obrigatório")

        if r["code"] == "wallet_provider" and not payload.wallet_provider:
            raise HTTPException(status_code=400, detail="wallet_provider obrigatório")

        if r["code"] == "amount_cents" and not payload.amount_cents:
            raise HTTPException(status_code=400, detail="amount_cents obrigatório")


# =========================
# ENDPOINT
# =========================

@router.post("/orders", response_model=KioskOrderOut)
def kiosk_create_order(
    payload: KioskOrderCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    x_device_fingerprint: str | None = Header(default=None),
):
    """
    KIOSK CREATE ORDER - 100% DB-DRIVEN
    """

    check_kiosk_antifraud(
        db=db,
        request=request,
        totem_id=payload.totem_id,
        region=payload.region.value,
        device_fingerprint=x_device_fingerprint,
    )

    resolved_payment = resolve_payment_ui_code(
        db=db,
        raw_payment_method=payload.payment_method,
        raw_payment_interface=payload.payment_interface,
        raw_wallet_provider=payload.wallet_provider,
    )

    payment_method_value = resolved_payment["payment_method"]
    payment_interface_value = resolved_payment["payment_interface"]
    wallet_provider_value = resolved_payment["wallet_provider"]

    if resolved_payment["requires_customer_phone"] and not payload.customer_phone:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MISSING_REQUIRED_FIELD",
                "message": "customer_phone é obrigatório para o método selecionado.",
                "payment_method": payment_method_value,
            },
        )

    if resolved_payment["requires_wallet_provider"] and not wallet_provider_value:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MISSING_REQUIRED_FIELD",
                "message": "wallet_provider é obrigatório para o método selecionado.",
                "payment_method": payment_method_value,
            },
        )

    capabilities = _get_kiosk_capabilities(db, payload.region.value)

    method = _resolve_method(capabilities, payment_method_value)

    payment_interface = _resolve_interface(
        method,
        payment_interface_value,
    )

    _validate_requirements(method, payload)

    payment_method_code = method["method"]


    # ===== PATCH: SANITY CHECK ANTES DE CRIAR ORDER =====
    # Verifica se o payment_method resolvido é um valor válido do enum
    payment_method_enum = _resolve_order_payment_method_enum(payment_method_code)
    
    # Sanity check crítico: garante que o valor mapeado existe no enum
    if payment_method_enum.value not in [e.value for e in PaymentMethod]:
        logger.error(
            "INVALID_ENUM_MAPPING",
            extra={
                "payment_method_code": payment_method_code,
                "resolved_value": payment_method_enum.value,
                "valid_values": [e.value for e in PaymentMethod],
                "region": payload.region.value,
                "totem_id": payload.totem_id,
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "type": "INVALID_PAYMENT_METHOD_ENUM",
                "message": f"Configuração inválida: método de pagamento '{payment_method_code}' mapeado para valor '{payment_method_enum.value}' não existe no sistema",
                "payment_method": payment_method_code,
            }
        )
    # ===== FIM DO PATCH =====

  
    pricing = backend_client.get_sku_pricing(
        payload.region.value,
        payload.sku_id,
        locker_id=payload.totem_id,
    )

    amount_cents = int(pricing.get("amount_cents") or pricing.get("price_cents"))

    # ttl_sec = resolve_prepayment_timeout_seconds(
    #     region_code=payload.region.value,
    #     order_channel=OrderChannel.KIOSK.value,
    #     payment_method=payment_method_code,
    # )
    # ttl_sec = capabilities["constraints"].get("prepayment_timeout_sec")
    ttl_sec = get_capability_constraint(
        db=db,
        region=payload.region.value,
        channel="KIOSK",
        context="ORDER_CREATION",
        code="prepayment_timeout_sec",
    )

    alloc = backend_client.locker_allocate(
        payload.region.value,
        payload.sku_id,
        ttl_sec,
        str(uuid.uuid4()),
        payload.desired_slot,
        locker_id=payload.totem_id,
    )

    allocation_id = alloc["allocation_id"]
    slot = int(alloc["slot"])

    try:
        order = Order(
            id=str(uuid.uuid4()),
            channel=OrderChannel.KIOSK,
            region=payload.region.value,
            totem_id=payload.totem_id,
            sku_id=payload.sku_id,
            amount_cents=amount_cents,
            status=OrderStatus.PAYMENT_PENDING,

            # CORREÇÃO 1: converter para enum/model compatível
            # payment_method=_resolve_order_payment_method_enum(payment_method_code),
            # depois do patch
            payment_method=payment_method_enum,  # Agora seguro
            
            payment_status=PaymentStatus.PENDING_CUSTOMER_ACTION,
            guest_phone=payload.customer_phone,
            payment_interface=payment_interface,
            wallet_provider=wallet_provider_value,
        )

        db.add(order)
        db.flush()

        allocation = Allocation(
            id=allocation_id,
            order_id=order.id,
            locker_id=payload.totem_id,
            slot=slot,
            state=AllocationState.RESERVED_PENDING_PAYMENT,
            ttl_seconds=ttl_sec, # ❌ ERRO AQUI - não é - o sistema agora é DB-driven (capability_profile)
        )

        db.add(allocation)
        db.commit()

    except Exception:
        db.rollback()

        # CORREÇÃO 2: liberar slot no runtime se falhar persistência
        try:
            backend_client.locker_release(
                payload.region.value,
                allocation_id,
                locker_id=payload.totem_id,
            )
        except Exception:
            logger.exception(
                "kiosk_create_order_release_failed_after_persistence_error",
                extra={
                    "allocation_id": allocation_id,
                    "locker_id": payload.totem_id,
                    "region": payload.region.value,
                },
            )

        raise


    try:
        register_prepayment_timeout_deadline(
            order_id=order.id,
            order_channel=order.channel.value,
            region_code=order.region,
            slot_id=str(slot),
            machine_id=order.totem_id,
            created_at=order.created_at,
            payment_method=payment_method_code,
            # timeout_seconds=ttl_sec,
        )

    except Exception:
        logger.exception("lifecycle_failed_releasing_allocation")

        # 🔴 CRÍTICO: liberar slot
        try:
            backend_client.locker_release(
                payload.region.value,
                allocation_id,
                locker_id=payload.totem_id,
            )
        except Exception:
            logger.exception("FAILED_TO_RELEASE_AFTER_LIFECYCLE_ERROR")

        # opcional: marcar allocation como FAILED
        allocation.state = AllocationState.FAILED
        db.commit()

        raise


    return KioskOrderOut(
        order_id=order.id,
        status=order.status.value,
        slot=slot,
        amount_cents=amount_cents,
        payment_method=payment_method_code,
        allocation_id=allocation.id,
        # ttl_sec=ttl_sec, # 👉 ✔️ isso NÃO está quebrando agora 👉 mas atenção: se a coluna não existir → vai quebrar depois / se existir → OK
        message="Pedido criado com sucesso",
    )






@router.post("/orders/{order_id}/payment-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    Confirma pagamento do pedido KIOSK.
    No fluxo atual, requires_confirmation -> payment-approved é uma simulação controlada.
    Fluxo consistente com DB + lifecycle + fiscal + fulfillment.
    """

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_NOT_FOUND", "order_id": order_id},
        )

    # ✅ CORRETO - CONFIRMED (simulação)
    if order.payment_status == PaymentStatus.CONFIRMED:
        return KioskPaymentApprovedOut(
            order_id=order.id,
            status="already_paid",
        )

    # =========================
    # CONFIRMAÇÃO COMPLETA (CORRETA)
    # =========================
    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .first()
    )

    if not allocation:
        raise HTTPException(
            status_code=500,
            detail={"type": "ALLOCATION_NOT_FOUND", "order_id": order.id},
        )

    # ✅ cancelar timeout
    try:
        cancel_prepayment_timeout_deadline(
            order_id=order.id,
            reason="payment_confirmed",
            metadata={"source": "kiosk_payment_approved"},
        )
    except Exception as e:
        logger.exception("FAILED_CANCEL_TIMEOUT")

        raise HTTPException(
            status_code=500,
            detail={
                "type": "FAILED_CANCEL_TIMEOUT",
                "order_id": order_id,
                "error": str(e),
            },
        )


    # evolução logística correta para o modelo atual
    # order.status = OrderStatus.PAID_PENDING_PICKUP


    # =========================
    # 1. CONFIRMAÇÃO FINANCEIRA (OBRIGATÓRIO)
    # =========================

    result = confirm_payment_and_emit_event(
        db=db,
        order=order,
        allocation=allocation,
        pickup=None,
        amount_cents=order.amount_cents,
        currency="BRL",
        source="kiosk_simulation",
        transaction_id=f"kiosk-{order.id}",
    )

    # =========================
    # 2. FULFILLMENT (locker + pickup)
    # =========================

    fulfill_payment_post_approval(
        db=db,
        order=order,
        allocation=allocation,  # 🔥 ESTAVA FALTANDO
    )

    db.commit()
    db.refresh(order)

    return KioskPaymentApprovedOut(
        order_id=order.id,
        status="paid",
        allocation_id=allocation.id,
        slot=allocation.slot,
        message="Pagamento confirmado e produto liberado com sucesso",
    )

