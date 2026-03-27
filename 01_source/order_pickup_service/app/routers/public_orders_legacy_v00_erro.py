# 01_source/order_pickup_service/app/routers/public_orders.py
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

# AJUSTE ESTE IMPORT para apontar para a função real já usada pelo endpoint interno /orders
# A ideia é: reaproveitar a MESMA regra de negócio, sem duplicação burra.
from app.services.order_service import create_online_order

router = APIRouter(prefix="/public", tags=["public-orders"])


class PublicCreateOrderRequest(BaseModel):
    region: str = Field(..., min_length=2, max_length=2)
    sku_id: str = Field(..., min_length=1)
    totem_id: str = Field(..., min_length=1)
    desired_slot: int = Field(..., ge=1)
    payment_method: str = Field(..., min_length=1)
    amount_cents: int | None = Field(default=None, ge=0)

    # opcionais por método
    card_type: str | None = None
    customer_phone: str | None = None
    wallet_provider: str | None = None


def _normalize_region(region: str) -> str:
    value = str(region or "").strip().upper()
    if value not in {"SP", "PT"}:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_REGION",
                "message": "region deve ser SP ou PT.",
                "region": region,
            },
        )
    return value


@router.post("/orders")
def create_public_order(
    payload: PublicCreateOrderRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    device_fp: str = Header(..., alias="X-Device-Fingerprint"),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """
    Cria pedido ONLINE público sem exigir Authorization.

    Headers obrigatórios:
    - Idempotency-Key
    - X-Device-Fingerprint

    Header opcional:
    - X-Request-ID

    Regras:
    - channel = ONLINE
    - não depende de usuário autenticado
    - reaproveita a mesma regra de negócio do endpoint interno
    """
    normalized_region = _normalize_region(payload.region)

    clean_payload = PublicCreateOrderRequest(
        region=normalized_region,
        sku_id=str(payload.sku_id).strip(),
        totem_id=str(payload.totem_id).strip(),
        desired_slot=int(payload.desired_slot),
        payment_method=str(payload.payment_method).strip().upper(),
        amount_cents=payload.amount_cents,
        card_type=str(payload.card_type).strip() if payload.card_type else None,
        customer_phone=str(payload.customer_phone).strip() if payload.customer_phone else None,
        wallet_provider=str(payload.wallet_provider).strip() if payload.wallet_provider else None,
    )

    if not clean_payload.totem_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "TOTEM_ID_REQUIRED",
                "message": "totem_id é obrigatório.",
            },
        )

    if not clean_payload.sku_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "SKU_ID_REQUIRED",
                "message": "sku_id é obrigatório.",
            },
        )

    try:
        return create_online_order(
            region=clean_payload.region,
            sku_id=clean_payload.sku_id,
            totem_id=clean_payload.totem_id,
            desired_slot=clean_payload.desired_slot,
            payment_method=clean_payload.payment_method,
            amount_cents=clean_payload.amount_cents,
            card_type=clean_payload.card_type,
            customer_phone=clean_payload.customer_phone,
            wallet_provider=clean_payload.wallet_provider,
            channel="ONLINE",
            request_id=request_id,
            idempotency_key=idempotency_key,
            device_fingerprint=device_fp,
            is_public=True,
            request=request,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "PUBLIC_ORDER_CREATE_FAILED",
                "message": str(exc),
                "channel": "ONLINE",
                "totem_id": clean_payload.totem_id,
                "desired_slot": clean_payload.desired_slot,
            },
        ) from exc