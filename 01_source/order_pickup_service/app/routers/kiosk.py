# 01_source/order_pickup_service/app/routers/kiosk.py
# CORRIGIDO: payment totalmente DB-driven (sem if / sem hardcoded)
# 06/04/2026 - import resolve_payment_ui_code
# 08/04/2026 - criação : def kiosk_payment_approved(
# 08/04/2026 - correção : OrderStatus.PAID para PaymentStatus.PAID
#              a correção mudou para PaymentStatus.CONFIRMED (ERRADA) 
#              a correção final é PaymentStatus.APPROVED (enum em Postgres)
# 08/04/2026 - order.status representa estado logístico e order.payment_status representa estado financeiro
# ALERTA/ATENÇÃO: SOBRE requires_confirmation PROBLEMA OCULTO (IMPORTANTE)
#                 → NÃO deveria chamar payment-approved
#                 → deveria aguardar confirmação do cliente (3DS / OTP / etc)
# Nesse momento o fluxo atual:
# requires_confirmation → frontend chama payment-approved, portanto, CONFIRMED é simulação. Isso é errado conceitualmente
# requires_confirmation → aguardar webhook / confirmação real. Isso é o correto
# 09/04/2026 - ADICIONADO SUPORTE A ATTEMPT (NÚMERO DE TENTATIVAS)
# 10/04/2026 - FIX CRÍTICO — PERSISTIR ALOCAÇÃO NO ORDER
# 13/04/2026 - CORREÇÃO FINAL — ORDEM DAS OPERAÇÕES (fulfill → deadline → confirmação)

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus, PaymentStatus, PaymentMethod
from app.models.pickup import Pickup, PickupChannel, PickupLifecycleStage, PickupStatus
from app.models.fiscal_document import FiscalDocument
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

from app.services.payment_confirm_service import (
    confirm_payment_and_emit_event,
    apply_payment_confirmation,
    emit_order_paid_and_simulate_fiscal,
)

from app.services.pickup_payment_fulfillment_service import (
    PickupPaymentFulfillmentService,
    fulfill_payment_post_approval,
)

from app.services.notification_dispatch_service import queue_receipt_email

from app.services.payment_capability_service import get_payment_capabilities

from app.services.payment_resolution_service import resolve_payment_ui_code

from app.services.capability_constraint_service import get_capability_constraint



router = APIRouter(prefix="/kiosk", tags=["kiosk"])

logger = logging.getLogger(__name__)


def _extract_attempt_from_fiscal(fiscal_payload: dict) -> int:
    """Extrai o número de tentativa do payload fiscal"""
    receipt_code = fiscal_payload.get("receipt_code", "")
    match = re.search(r'-ATT(\d{2})', receipt_code)
    if match:
        return int(match.group(1))
    return 1


# =========================
# CAPABILITY HELPERS (DB-DRIVEN)
# =========================


def _resolve_order_payment_method_enum(method_code: str) -> PaymentMethod:
    raw = str(method_code or "").strip()

    mapping = {
        "creditCard": PaymentMethod.creditCard,
        "debitCard": PaymentMethod.debitCard,
        "giftCard": PaymentMethod.giftCard,
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
        # channel="KIOSK",
        # context="ORDER_CREATION",
        channel="kiosk",
        context="order_creation",
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

@router.post("/identify", response_model=KioskIdentifyOut)
def kiosk_identify(
    payload: KioskCustomerIdentifyIn,
    db: Session = Depends(get_db),
):
    order = db.get(Order, payload.order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_NOT_FOUND", "order_id": payload.order_id},
        )

    # salva dados no pedido
    if payload.email:
        order.receipt_email = payload.email

    if payload.phone:
        order.receipt_phone = payload.phone

    db.commit()

    # buscar último fiscal do pedido
    existing_fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .order_by(FiscalDocument.attempt.desc())
        .first()
    )

    receipt_code = None
    if existing_fiscal and existing_fiscal.receipt_code:
        receipt_code = existing_fiscal.receipt_code
    else:
        # receipt_code = f"SIM-{order.id[:8].upper()}"
        if not existing_fiscal or not existing_fiscal.receipt_code:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "FISCAL_NOT_AVAILABLE",
                    "order_id": order.id,
                },
            )

    # dispara envio (fila)
    try:
        queue_receipt_email(
            db=db,
            # order=order,
            order_id=order.id,
            email=payload.email,
            # receipt_code=payload.receipt_code,
            receipt_code=receipt_code,
        )
    except Exception:
        logger.exception("FAILED_TO_QUEUE_RECEIPT_EMAIL")

    return KioskIdentifyOut(
        ok=True,
        order_id=order.id,
        # email=payload.email,
        # phone=payload.phone,
        message="Identificação registrada e envio do comprovante solicitado",
    )



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
    payment_method_enum = _resolve_order_payment_method_enum(payment_method_code)
    
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

    # =========================
    # NOVO FLOW UNIFICADO
    # =========================
    try:
        logger.error("🔥 NEW FLOW EXECUTADO - kiosk.py chamando service")

        if not payload.amount_cents:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "AMOUNT_CENTS_REQUIRED",
                    "message": "amount_cents é obrigatório no KIOSK",
                },
            )

        service_payload = {
            "region": payload.region.value,
            "locker_id": payload.totem_id,
            "totem_id": payload.totem_id,
            "sku_id": payload.sku_id,
            "slot": payload.desired_slot,
            "payment_method": payment_method_code,
            # "amount_cents": None,  # causando erro - deveria ser resolvido no backend se necessário
            "amount_cents": payload.amount_cents,
            "payment_interface": payment_interface,
            "wallet_provider": wallet_provider_value,
            "customer_phone": payload.customer_phone,
            "device_id": x_device_fingerprint,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        result = PickupPaymentFulfillmentService().create_kiosk_order_with_payment(
            db,
            service_payload
        )

        logger.error("🔥 NEW FLOW EXECUTADO - kiosk.py retorno do service")

    except Exception as exc:
        logger.exception("KIOSK_CREATE_ORDER_FAILED")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "KIOSK_CREATE_ORDER_FAILED",
                "error": str(exc),
            },
        )

    # =========================
    # RESPONSE DIRETO DO SERVICE
    # =========================
    return KioskOrderOut(
        order_id=result["order_id"],
        allocation_id=result.get("allocation_id"),
        slot=result.get("slot"),
        amount_cents=result["amount_cents"],
        payment_method=result.get("payment_method"),
        payment_status=result.get("payment_status"),
        instruction_type=result.get("instruction_type"),
        ttl_sec=result.get("ttl_sec"),
        expires_at=result.get("expires_at"),
        qr_code=result.get("qr_code"),
        qr_code_text=result.get("qr_code_text"),
        status="PAYMENT_PENDING" if result.get("payment_status") != "FAILED" else "CANCELLED",
        message="Pedido criado e aguardando pagamento" if result.get("payment_status") != "FAILED" else "Falha ao iniciar pagamento; gaveta liberada",
    )


# =============================================================
# FIX: _finalize_kiosk_payment — kiosk.py
# Data: 2026-04-13
# Bugs corrigidos:
#   1. order.status = OrderStatus.FAILED quebrava db.flush() porque
#      'FAILED' não existia no enum orderstatus do PostgreSQL.
#      → Solução: rodar migration_add_failed_to_orderstatus.sql
#        E remover db.flush() do bloco de realloc_error (flush dentro
#        de except gera sessão suja mesmo com enum correto).
#   2. except Exception as state_error engolia a exceção (inclusive
#      HTTPException do bloco interno) e continuava execução com
#      sessão SQLAlchemy em estado de rollback pendente.
#      → Solução: re-raise HTTPException explicitamente;
#        para outros erros, db.rollback() + re-raise.
# =============================================================

def _finalize_kiosk_payment(
    *,
    order: Order,
    db: Session,
    source: str,
    allow_force_confirm: bool,
) -> KioskPaymentApprovedOut:

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

    # fluxo real: só prossegue se já aprovado financeiramente
    if not allow_force_confirm and order.payment_status != PaymentStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "PAYMENT_NOT_APPROVED",
                "order_id": order.id,
                "payment_status": order.payment_status.value,
            },
        )

    # -----------------------------------------------------------------
    # Verifica estado da alocação no backend ANTES do fulfillment
    # FIX: separa except HTTPException do except genérico para não
    #      engolir erros reais. db.rollback() antes de re-raise garante
    #      sessão limpa para quem chamar acima.
    # -----------------------------------------------------------------
    try:
        state = backend_client.get_allocation_state(
            allocation.id,
            locker_id=order.totem_id
        )

        logger.info(f"Allocation state check: {state} for allocation {allocation.id}")

        if state in ["RELEASED", "EXPIRED", "NOT_FOUND"]:
            logger.warning(f"Allocation lost, attempting reallocation for order {order.id}")

            try:
                request_id = str(uuid.uuid4())
                new_alloc = backend_client.locker_allocate(
                    order.region,
                    order.sku_id,
                    ttl_sec=900,  # 15 minutos
                    request_id=request_id,
                    desired_slot=int(allocation.slot),
                    locker_id=order.totem_id,
                )

                # Atualiza alocação no banco — flush só aqui (sem erros pendentes)
                allocation.id = new_alloc["allocation_id"]
                allocation.state = AllocationState.RESERVED_PENDING_PAYMENT
                db.flush()

                logger.info(f"Successfully reallocated same slot {allocation.slot} for order {order.id}")

            except Exception as realloc_error:
                logger.error(f"Failed to reallocate slot for order {order.id}: {realloc_error}")

                # FIX 1: NÃO chamar db.flush() aqui — sessão pode estar suja.
                # FIX 2: NÃO setar order.status = OrderStatus.FAILED antes da
                #         migration_add_failed_to_orderstatus.sql ser aplicada.
                #         Após a migration, pode reabilitar a linha abaixo se quiser:
                #
                #   order.status = OrderStatus.FAILED
                #
                # Por ora, rollback limpa a sessão antes de lançar a HTTPException.
                db.rollback()

                raise HTTPException(
                    status_code=409,
                    detail={
                        "type": "ALLOCATION_LOST_CANNOT_REALLOCATE",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "slot": allocation.slot,
                        "message": "A gaveta não está mais disponível e não foi possível realocar. Por favor, crie um novo pedido.",
                    }
                )

    except HTTPException:
        # FIX: re-raise HTTPException gerada dentro do bloco acima.
        # O except genérico abaixo NÃO deve capturá-la.
        raise

    except Exception as state_error:
        # Erro de comunicação com o serviço de estado (rede, timeout, etc.)
        # FIX: db.rollback() garante sessão limpa; re-raise para não
        #      continuar com sessão em estado indeterminado.
        logger.error(f"Error checking allocation state: {state_error}")
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "type": "ALLOCATION_STATE_CHECK_FAILED",
                "order_id": order.id,
                "message": "Não foi possível verificar o estado da gaveta. Tente novamente.",
                "error": str(state_error),
            }
        )

    # -----------------------------------------------------------------
    # fulfillment PRIMEIRO (abre gaveta, cria pickup)
    # -----------------------------------------------------------------
    try:
        fulfill_result = fulfill_payment_post_approval(
            db=db,
            order=order,
            allocation=allocation,
        )
    except RuntimeError as e:
        error_dict = e.args[0] if e.args else {}
        if error_dict.get('type') == 'ALLOCATION_LOST':
            logger.error(f"Allocation lost during fulfillment: {error_dict}")
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "ALLOCATION_LOST",
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "message": "A reserva da gaveta expirou. Por favor, crie um novo pedido.",
                }
            )
        raise

    # -----------------------------------------------------------------
    # Cancela deadline DEPOIS do fulfill
    # -----------------------------------------------------------------
    try:
        cancel_prepayment_timeout_deadline(
            order_id=order.id,
            reason="payment_confirmed" if not allow_force_confirm else "payment_simulated_confirmed",
            metadata={"source": source},
        )
    except Exception:
        logger.exception("FAILED_CANCEL_TIMEOUT")
        # Não interrompe fluxo — fulfillment já foi confirmado

    # -----------------------------------------------------------------
    # Confirmação financeira por último (apenas no modo simulação)
    # -----------------------------------------------------------------
    if allow_force_confirm and order.payment_status != PaymentStatus.APPROVED:
        apply_payment_confirmation(
            db=db,
            order=order,
            transaction_id=f"sim-{order.id}",
            payment_method=order.payment_method,
            amount_cents=order.amount_cents,
            currency=order.currency or "BRL",
            source="simulation",
        )

    # -----------------------------------------------------------------
    # Pickup (upsert)
    # -----------------------------------------------------------------
    existing_pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .first()
    )

    if existing_pickup:
        pickup = existing_pickup
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        pickup.locker_id = allocation.locker_id
        pickup.slot = allocation.slot
        pickup.region = order.region
        pickup.ready_at = pickup.ready_at or datetime.utcnow()
        pickup.touch()
    else:
        pickup = Pickup(
            id=str(uuid.uuid4()),
            order_id=order.id,
            channel=PickupChannel.KIOSK,
            region=order.region,
            locker_id=allocation.locker_id,
            machine_id=allocation.locker_id,
            slot=allocation.slot,
            status=PickupStatus.ACTIVE,
            lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
            ready_at=datetime.utcnow(),
        )
        db.add(pickup)
        db.flush()

    # -----------------------------------------------------------------
    # Attempt fiscal
    # -----------------------------------------------------------------
    existing_fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .order_by(FiscalDocument.attempt.desc())
        .first()
    )

    attempt = 1
    if existing_fiscal and existing_fiscal.payload_json:
        payload_json = existing_fiscal.payload_json
        if isinstance(payload_json, dict):
            attempt = _extract_attempt_from_fiscal(payload_json) + 1

    financial = emit_order_paid_and_simulate_fiscal(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        amount_cents=order.amount_cents,
        currency=order.currency or "BRL",
        source=source,
        transaction_id=order.gateway_transaction_id,
        skip_locker_commit=True,
        attempt=attempt,
    )

    fiscal = financial["fiscal"]

    if not fiscal:
        raise HTTPException(
            status_code=500,
            detail={"type": "FISCAL_MISSING", "order_id": order.id},
        )

    existing_fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .order_by(FiscalDocument.attempt.desc())
        .first()
    )

    if not fiscal.get("receipt_code") and existing_fiscal and existing_fiscal.receipt_code:
        fiscal["receipt_code"] = existing_fiscal.receipt_code

    db.commit()
    db.refresh(order)

    return KioskPaymentApprovedOut(
        order_id=order.id,
        slot=allocation.slot,
        status="paid",
        allocation_id=allocation.id,
        payment_method=order.payment_method,
        receipt_code=fiscal.get("receipt_code"),
        receipt_print_path=fiscal.get("print_site_path"),
        receipt_json_path=fiscal.get("json_site_path"),
        message=(
            "Pagamento confirmado e produto liberado com sucesso"
            if not allow_force_confirm
            else "Pagamento simulado e produto liberado com sucesso"
        ),
    )




# Endpoint real
@router.post("/orders/{order_id}/payment-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    Fluxo real: só confirma quando o pedido já estiver financeiramente CONFIRMED.
    """

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_NOT_FOUND", "order_id": order_id},
        )

    if order.payment_status == PaymentStatus.APPROVED:
        return _finalize_kiosk_payment(
            order=order,
            db=db,
            source="kiosk_payment_approved",
            allow_force_confirm=False,
        )

    raise HTTPException(
        status_code=400,
        detail={
            "type": "PAYMENT_NOT_APPROVED",
            "order_id": order.id,
            "payment_status": order.payment_status.value,
            "message": "Pagamento ainda não aprovado financeiramente. Use o endpoint simulado apenas em ambiente de desenvolvimento.",
        },
    )


# Endpoint simulado
@router.post("/orders/{order_id}/payment-simulate-approved", response_model=KioskPaymentApprovedOut)
def kiosk_payment_simulate_approved(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    Fluxo de desenvolvimento/simulação:
    força confirmação financeira local para concluir o fluxo KIOSK.
    """

    # 🔥 1. buscar order primeiro
    order = db.get(Order, order_id)

    if order.status == OrderStatus.DISPENSED:
        return {"status": "already_processed"}

    if not order:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_NOT_FOUND", "order_id": order_id},
        )

    if order.payment_status == "FAILED" or order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ORDER_NOT_PAYABLE",
                "message": "Pedido já falhou ou foi cancelado. Crie um novo pedido.",
                "order_id": order_id,
            },
        )

    # 🔥 seguir fluxo normal (sem duplicar cancel_prepayment_timeout_deadline)
    return _finalize_kiosk_payment(
        order=order,
        db=db,
        source="kiosk_payment_simulate_approved",
        allow_force_confirm=True,
    )

