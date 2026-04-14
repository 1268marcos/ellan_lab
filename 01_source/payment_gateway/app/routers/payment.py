# 01_source/payment_gateway/app/routers/payment.py
# 13/04/2026 - CORRIGIDO: Adicionados endpoints POST /gateway/payment/create
#              e POST /gateway/pagamento (legado frontend) que chamam process_payment()

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from app.models.payment_model import PaymentRequest
from app.services.payment_service import process_payment
from app.schemas.payment import CancelPaymentRequest
from app.core.config import settings
from app.core.event_log import GatewayEventLogger

router = APIRouter(tags=["Payment"])


def _gen_idempotency_key() -> str:
    return f"auto_{uuid.uuid4().hex}"


def _gen_device_fp() -> str:
    return f"fp_auto_{uuid.uuid4().hex[:16]}"


def _get_logger():
    try:
        log_dir = getattr(settings, "GATEWAY_LOG_DIR", "/logs")
        log_hash_salt = getattr(settings, "LOG_HASH_SALT", None)
        if not log_hash_salt:
            return None
        return GatewayEventLogger(
            gateway_id=getattr(settings, "GATEWAY_ID", "payment_gateway"),
            log_dir=log_dir,
            log_hash_salt=log_hash_salt,
        )
    except Exception as e:
        print(f"Warning: Failed to initialize logger: {e}")
        return None


# ---------------------------------------------------------------------------
# Endpoint principal — chamado pelo order_pickup_service via PaymentGatewayClient
# Paths em ordem de preferência no _candidate_paths() do client:
#   /gateway/payment/create  ← primeira tentativa
#   /gateway/payments/create
#   /payments/create
#   /payments
#   /gateway/payment
# ---------------------------------------------------------------------------

def _handle_payment(data: PaymentRequest, request: Request, idempotency_key: str, device_fp: str):
    result = process_payment(
        data=data,
        request=request,
        idempotency_key=idempotency_key,
        device_fp=device_fp,
        request_id=None,
    )
    return result


@router.post("/gateway/payment/create", response_model=None)
async def create_payment_new(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)


@router.post("/gateway/payments/create", response_model=None)
async def create_payment_plural(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)


@router.post("/payments/create", response_model=None)
async def create_payment_short(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)


@router.post("/payments", response_model=None)
async def create_payment_root(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)


@router.post("/gateway/payment", response_model=None)
async def create_payment_legacy_path(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)


# ---------------------------------------------------------------------------
# Endpoint legado — chamado diretamente pelo frontend
# ---------------------------------------------------------------------------

@router.post("/gateway/pagamento", response_model=None)
async def gateway_pagamento(
    data: PaymentRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    device_fp: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    ik = idempotency_key or _gen_idempotency_key()
    fp = device_fp or _gen_device_fp()
    return _handle_payment(data, request, ik, fp)

#-------------------------------
# CHATGPT 
# from app.integrations.payments.base.contracts import CreatePaymentCommand
# from fastapi import APIRouter
# 
# router = APIRouter(prefix="/gateway", tags=["gateway"])
# 
# 
# @router.post("/payment_gpt")
# def create_payment_gpt(payload: dict):
#     """
#     Endpoint mínimo para criação de pagamento (stub funcional)
#     """
# 
#     order_id = payload.get("order_id")
#     amount = payload.get("amount")
#     currency = payload.get("currency", "BRL")
# 
#     if not order_id or not amount:
#         return {
#             "status": "error",
#             "message": "order_id e amount são obrigatórios"
#         }
# 
#     # 🔥 SIMULA PIX
#     return {
#         "provider": "stub",
#         "provider_payment_id": f"pay_{order_id}",
#         "status": "PENDING",
#         "qr_code": f"QR_CODE_{order_id}",
#         "qr_code_text": f"PIX_CODE_{order_id}",
#         "redirect_url": None
#     }

