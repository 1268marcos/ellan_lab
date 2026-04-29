# 01_source/order_pickup_service/app/routers/public_orders.py
# PATCH DIRETO — KIOSK CREATE ORDER + PAYMENT INSTRUCTION NO RESPONSE
# 13/04/2026

# 14/04/2026 - Não continue remendando o public_orders.py atual de 13/04.
# Ele mistura ONLINE com KIOSK e foi essa mistura que gerou a cascata de 
# problemas: canal errado, schema de payment_instructions, 404 no 
# detalhe e fluxo público quebrado.


from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List, Dict
import hashlib
import secrets
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.auth_dep import get_current_public_user, get_current_user
from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument
from app.models.order import Order, OrderStatus, PaymentMethod, OrderChannel
from app.models.user import User
from app.models.allocation import Allocation
from app.schemas.orders import CreateOrderIn, OnlineRegion, OnlinePaymentMethod
from app.services.order_creation_service import create_order_core, CreateOrderCoreResult
from app.services.payment_resolution_service import resolve_payment_ui_code
from app.services.pickup_payment_fulfillment_service import PickupPaymentFulfillmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/orders", tags=["public-orders"])


# =========================================================
# HELPERS
# =========================================================

def _dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _enum_value(value):
    if value is None:
        return None
    return getattr(value, "value", value)


def _get_latest_payment_instruction(db: Session, order_id: str) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT
                id,
                order_id,
                instruction_type,
                amount_cents,
                currency,
                status,
                expires_at,
                qr_code,
                qr_code_text,
                authorization_code,
                captured_at,
                redirect_url,
                provider_payment_id,
                provider_name,
                created_at,
                updated_at
            FROM payment_instructions
            WHERE order_id = :order_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).mappings().first()

    return dict(row) if row else None


def _serialize_order(
    order: Order,
    fiscal: FiscalDocument | None = None,
    payment_instruction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = {
        "id": order.id,
        "order_id": order.id,
        "user_id": order.user_id,
        "channel": _enum_value(order.channel),
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": order.sku_id,
        "amount_cents": order.amount_cents,
        "status": _enum_value(order.status),
        "gateway_transaction_id": order.gateway_transaction_id,
        "payment_method": _enum_value(order.payment_method),
        "payment_status": _enum_value(order.payment_status),
        "card_type": _enum_value(order.card_type),
        "payment_updated_at": _dt_iso(order.payment_updated_at),
        "paid_at": _dt_iso(order.paid_at),
        "pickup_deadline_at": _dt_iso(order.pickup_deadline_at),
        "picked_up_at": _dt_iso(order.picked_up_at),
        "guest_session_id": order.guest_session_id,
        "receipt_email": order.receipt_email,
        "receipt_phone": order.receipt_phone,
        "guest_phone": order.guest_phone,
        "guest_email": order.guest_email,
        "created_at": _dt_iso(order.created_at),
        "updated_at": _dt_iso(order.updated_at),
        "currency": order.currency,
        "site_id": getattr(order, "site_id", None),
        "tenant_id": getattr(order, "tenant_id", None),
        "ecommerce_partner_id": getattr(order, "ecommerce_partner_id", None),
        "partner_order_ref": getattr(order, "partner_order_ref", None),
        "sku_description": getattr(order, "sku_description", None),
        "slot_size": getattr(order, "slot_size", None),
        "card_last4": getattr(order, "card_last4", None),
        "card_brand": getattr(order, "card_brand", None),
        "installments": getattr(order, "installments", None),
        "guest_name": getattr(order, "guest_name", None),
        "cancelled_at": _dt_iso(getattr(order, "cancelled_at", None)),
        "cancel_reason": getattr(order, "cancel_reason", None),
        "refunded_at": _dt_iso(getattr(order, "refunded_at", None)),
        "refund_reason": getattr(order, "refund_reason", None),
        "payment_interface": getattr(order, "payment_interface", None),
        "wallet_provider": getattr(order, "wallet_provider", None),
        "device_id": getattr(order, "device_id", None),
        "ip_address": getattr(order, "ip_address", None),
        "user_agent": getattr(order, "user_agent", None),
        "slot": getattr(order, "slot", None),
        "allocation_id": getattr(order, "allocation_id", None),
        "allocation_expires_at": _dt_iso(getattr(order, "allocation_expires_at", None)),
        "fiscal": None,
        "instruction_type": None,
        "ttl_sec": None,
        "expires_at": None,
        "qr_code": None,
        "qr_code_text": None,
        "redirect_url": None,
        "provider_payment_id": None,
        "provider_name": None,
        "payment_instruction_status": None,
    }

    if fiscal is not None:
        response["fiscal"] = {
            "id": fiscal.id,
            "order_id": fiscal.order_id,
            "receipt_code": getattr(fiscal, "receipt_code", None),
            "attempt": getattr(fiscal, "attempt", None),
            "issued_at": _dt_iso(getattr(fiscal, "issued_at", None)),
            "status": _enum_value(getattr(fiscal, "status", None)),
        }

    if payment_instruction:
        expires_at = payment_instruction.get("expires_at")
        created_at = payment_instruction.get("created_at")

        ttl_sec = None
        if expires_at and created_at:
            try:
                ttl_sec = int((expires_at - created_at).total_seconds())
            except Exception:
                ttl_sec = None

        response.update(
            {
                "instruction_type": payment_instruction.get("instruction_type"),
                "ttl_sec": ttl_sec,
                "expires_at": _dt_iso(expires_at),
                "qr_code": payment_instruction.get("qr_code"),
                "qr_code_text": payment_instruction.get("qr_code_text"),
                "redirect_url": payment_instruction.get("redirect_url"),
                "provider_payment_id": payment_instruction.get("provider_payment_id"),
                "provider_name": payment_instruction.get("provider_name"),
                "payment_instruction_status": payment_instruction.get("status"),
            }
        )

    return response


# =========================================================
# SCHEMAS
# =========================================================

class KioskOrderCreateIn(BaseModel):
    region: OnlineRegion
    totem_id: str = Field(..., min_length=3, max_length=120)
    sku_id: str = Field(..., min_length=1, max_length=120)
    slot: int = Field(..., ge=1)
    payment_method: str = Field(..., min_length=1, max_length=80)
    amount_cents: int | None = Field(default=None, ge=1)
    customer_phone: str | None = None
    payment_interface: str | None = None
    wallet_provider: str | None = None

    @field_validator("totem_id", "sku_id", "payment_method", mode="before")
    @classmethod
    def _strip_text(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @field_validator("customer_phone", "payment_interface", "wallet_provider", mode="before")
    @classmethod
    def _strip_optional(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        return value or None


class KioskOrderOut(BaseModel):
    order_id: str
    allocation_id: str | None = None
    slot: int | None = None
    amount_cents: int
    payment_method: str | None = None
    payment_status: str | None = None
    instruction_type: str | None = None
    ttl_sec: int | None = None
    expires_at: str | None = None
    qr_code: str | None = None
    qr_code_text: str | None = None
    redirect_url: str | None = None
    status: str | None = None


class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    email: str | None = None
    phone: str | None = None


class KioskIdentifyOut(BaseModel):
    ok: bool
    order_id: str
    message: str


# =========================================================
# PLACEHOLDERS COMPAT
# =========================================================

def check_kiosk_antifraud(
    db: Session,
    request: Request,
    totem_id: str,
    region: str,
    device_fingerprint: str | None = None,
):
    return None


def queue_receipt_email(
    db: Session,
    order_id: str,
    email: str | None,
    receipt_code: str | None,
):
    return None


def _resolve_payment_interface(resolved_payment: dict[str, Any]) -> str | None:
    interfaces = resolved_payment.get("interfaces") or []
    if not interfaces:
        return None

    default = next((i for i in interfaces if i.get("default")), None)
    if default:
        return default.get("code")

    return interfaces[0].get("code")


def _validate_requirements(method: dict[str, Any], payload: KioskOrderCreateIn):
    for r in method.get("requirements", []):
        if not r.get("required"):
            continue

        code = r.get("code")

        if code == "customer_phone" and not payload.customer_phone:
            raise HTTPException(status_code=400, detail="customer_phone obrigatório")

        if code == "wallet_provider" and not payload.wallet_provider:
            raise HTTPException(status_code=400, detail="wallet_provider obrigatório")

        if code == "amount_cents" and not payload.amount_cents:
            raise HTTPException(status_code=400, detail="amount_cents obrigatório")


# =========================================================
# IDENTIFY
# =========================================================

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

    if payload.email:
        order.receipt_email = payload.email

    if payload.phone:
        order.receipt_phone = payload.phone

    db.commit()

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
        raise HTTPException(
            status_code=409,
            detail={
                "type": "FISCAL_NOT_AVAILABLE",
                "order_id": order.id,
            },
        )

    try:
        queue_receipt_email(
            db=db,
            order_id=order.id,
            email=payload.email,
            receipt_code=receipt_code,
        )
    except Exception:
        logger.exception("FAILED_TO_QUEUE_RECEIPT_EMAIL")

    return KioskIdentifyOut(
        ok=True,
        order_id=order.id,
        message="Identificação registrada e envio do comprovante solicitado",
    )


# =========================================================
# KIOSK CREATE ORDER
# =========================================================

@router.post("/", response_model=KioskOrderOut)
@router.post("/orders", response_model=KioskOrderOut)
def kiosk_create_order(
    payload: KioskOrderCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    x_device_fingerprint: str | None = Header(default=None),
):
    check_kiosk_antifraud(
        db=db,
        request=request,
        totem_id=payload.totem_id,
        region=payload.region.value,
        device_fingerprint=x_device_fingerprint,
    )

    resolved_payment = resolve_payment_ui_code(
        db=db,
        # region=payload.region.value,
        # channel="KIOSK",
        # context="LOCKER",
        # ui_code=payload.payment_method,
        # locker_id=payload.totem_id,
        raw_payment_method=payload.payment_method,
        raw_payment_interface=payload.payment_interface,
        raw_wallet_provider=payload.wallet_provider,
    )

    if not resolved_payment:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "PAYMENT_METHOD_NOT_ALLOWED",
                "payment_method": payload.payment_method,
                "region": payload.region.value,
                "totem_id": payload.totem_id,
            },
        )

    _validate_requirements(resolved_payment, payload)

    # resolved_method = (
    #     resolved_payment.get("method")
    #     or resolved_payment.get("payment_method")
    #     or payload.payment_method
    # )

    resolved_method = resolved_payment["payment_method"]

    # resolved_interface = (
    #     payload.payment_interface
    #     or _resolve_payment_interface(resolved_payment)
    # )

    resolved_interface = resolved_payment.get("payment_interface")

    if not payload.amount_cents:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "AMOUNT_CENTS_REQUIRED",
                "message": "amount_cents é obrigatório para criação do pedido KIOSK",
            },
        )

    service_payload = {
        "region": payload.region.value,
        "locker_id": payload.totem_id,
        "totem_id": payload.totem_id,
        "sku_id": payload.sku_id,
        "slot": payload.slot,
        "payment_method": resolved_method,
        "amount_cents": payload.amount_cents,
        "payment_interface": resolved_interface,
        "wallet_provider": payload.wallet_provider,
        "customer_phone": payload.customer_phone,
        "device_id": x_device_fingerprint,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    try:
        logger.error("🔥 NEW FLOW EXECUTADO - em public_orders.py antes do result = PickupPaymentFulfillmentService")
        # result = PickupPaymentFulfillmentService().create_kiosk_order_with_payment(service_payload)
        result = PickupPaymentFulfillmentService().create_kiosk_order_with_payment(db, service_payload)
        logger.error("🔥 NEW FLOW EXECUTADO - em public_orders.py depois do result = PickupPaymentFulfillmentService")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("KIOSK_CREATE_ORDER_FAILED")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "KIOSK_CREATE_ORDER_FAILED",
                "message": "Falha ao criar pedido KIOSK com payment_instruction",
                "region": payload.region.value,
                "totem_id": payload.totem_id,
                "slot": payload.slot,
                "sku_id": payload.sku_id,
                "payment_method": resolved_method,
                "error_type": exc.__class__.__name__,
            },
        ) from exc

    order = db.get(Order, result["order_id"])
    if order is None:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "ORDER_NOT_PERSISTED",
                "order_id": result["order_id"],
            },
        )

    payment_instruction = _get_latest_payment_instruction(db, order.id)

    response = _serialize_order(
        order=order,
        fiscal=None,
        payment_instruction=payment_instruction,
    )

    response["allocation_id"] = result.get("allocation_id") or response.get("allocation_id")
    response["slot"] = result.get("slot") or response.get("slot")
    response["amount_cents"] = result.get("amount_cents") or response.get("amount_cents")
    response["payment_method"] = result.get("payment_method") or response.get("payment_method")
    response["payment_status"] = result.get("payment_status") or response.get("payment_status")
    response["instruction_type"] = result.get("instruction_type") or response.get("instruction_type")
    response["ttl_sec"] = result.get("ttl_sec") or response.get("ttl_sec")
    response["expires_at"] = result.get("expires_at") or response.get("expires_at")
    response["qr_code"] = result.get("qr_code") or response.get("qr_code")
    response["qr_code_text"] = result.get("qr_code_text") or response.get("qr_code_text")
    response["redirect_url"] = result.get("redirect_url") or response.get("redirect_url")

    return KioskOrderOut(
        order_id=response["order_id"],
        allocation_id=response.get("allocation_id"),
        slot=response.get("slot"),
        amount_cents=response["amount_cents"],
        payment_method=response.get("payment_method"),
        payment_status=response.get("payment_status"),
        instruction_type=response.get("instruction_type"),
        ttl_sec=response.get("ttl_sec"),
        expires_at=response.get("expires_at"),
        qr_code=response.get("qr_code"),
        qr_code_text=response.get("qr_code_text"),
        redirect_url=response.get("redirect_url"),
        status=response.get("status"),
    )


@router.get("/{order_id}")
def get_public_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_public_user),
):
    # 🔥 ALTERAÇÃO: Verificar se o usuário está autenticado
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "AUTHENTICATION_REQUIRED",
                "message": "É necessário estar autenticado para recuperar pedidos.",
            },
        )

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "order_id": order_id,
            },
        )

    payment_instruction = _get_latest_payment_instruction(db, order.id)

    fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .order_by(FiscalDocument.created_at.desc())
        .first()
    )

    return _serialize_order(
        order=order,
        fiscal=fiscal,
        payment_instruction=payment_instruction,
    )