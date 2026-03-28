# 01_source/order_pickup_service/app/routers/public_orders.py
from __future__ import annotations

from datetime import datetime
from typing import Any
import hashlib
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user, get_current_user  # 🔥 ALTERAÇÃO: Importar get_current_user do auth_dep

from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.orders import CreateOrderIn, OrderOut
from app.services.order_creation_service import create_order_core


router = APIRouter(prefix="/public/orders", tags=["public-orders"])


def _dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize_order(order: Order, fiscal: FiscalDocument | None = None) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_id": order.id,
        "user_id": order.user_id,
        "channel": order.channel.value if order.channel else None,
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": order.sku_id,
        "amount_cents": order.amount_cents,
        "status": order.status.value if order.status else None,
        "gateway_transaction_id": order.gateway_transaction_id,
        "payment_method": order.payment_method.value if order.payment_method else None,
        "payment_status": order.payment_status.value if order.payment_status else None,
        "card_type": order.card_type.value if order.card_type else None,
        "payment_updated_at": _dt_iso(order.payment_updated_at),
        "paid_at": _dt_iso(order.paid_at),
        "pickup_deadline_at": _dt_iso(order.pickup_deadline_at),
        "picked_up_at": _dt_iso(order.picked_up_at),
        "guest_session_id": order.guest_session_id,
        "consent_marketing": order.consent_marketing,
        "created_at": _dt_iso(order.created_at),
        "updated_at": _dt_iso(order.updated_at),
        "receipt_code": fiscal.receipt_code if fiscal else None,
        "receipt_print_path": fiscal.print_site_path if fiscal else None,
        "receipt_json_path": (
            f"/public/fiscal/by-code/{fiscal.receipt_code}" if fiscal else None
        ),
        "public_access_enabled": bool(getattr(order, "public_access_token_hash", None)),
    }


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_public_access_token() -> str:
    return secrets.token_urlsafe(32)


def generate_public_token():
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

class PublicCreateOrderRequest(BaseModel):
    region: str = Field(..., min_length=2, max_length=8)
    sku_id: str = Field(..., min_length=1, max_length=255)
    totem_id: str = Field(..., min_length=1, max_length=255)
    desired_slot: int = Field(..., ge=1, le=999)
    payment_method: str = Field(..., min_length=1, max_length=64)
    amount_cents: int | None = Field(default=None, ge=1)
    card_type: str | None = Field(default=None, max_length=32)
    customer_phone: str | None = Field(default=None, max_length=64)
    wallet_provider: str | None = Field(default=None, max_length=64)
    consent_marketing: bool = False


def _resolve_guest_session_id(device_fp: str | None) -> str | None:
    value = str(device_fp or "").strip()
    return value or None


def _get_order_for_public_access(
    *,
    db: Session,
    order_id: str,
    current_user: User | None,
    guest_session_id: str | None,
    public_token: str | None,
) -> Order | None:
    base_query = db.query(Order).filter(Order.id == order_id)

    if current_user is not None:
        order = base_query.filter(Order.user_id == current_user.id).first()
        if order:
            return order

    if guest_session_id:
        order = base_query.filter(Order.guest_session_id == guest_session_id).first()
        if order:
            return order

    if public_token:
        order = (
            base_query
            .filter(Order.public_access_token_hash == _hash_token(public_token))
            .first()
        )
        if order:
            return order

    return None


def _list_orders_for_public_access(
    *,
    db: Session,
    current_user: User | None,
    guest_session_id: str | None,
    limit: int,
    offset: int,
    status_value: str | None,
) -> tuple[list[Order], int]:
    if current_user is None and not guest_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "PUBLIC_ORDER_ACCESS_DENIED",
                "message": (
                    "Informe autenticação pública válida ou X-Device-Fingerprint "
                    "para acessar pedidos públicos."
                ),
            },
        )

    query = db.query(Order)

    if current_user is not None and guest_session_id:
        query = query.filter(
            (Order.user_id == current_user.id) | (Order.guest_session_id == guest_session_id)
        )
    elif current_user is not None:
        query = query.filter(Order.user_id == current_user.id)
    else:
        query = query.filter(Order.guest_session_id == guest_session_id)

    if status_value:
        try:
            status_enum = OrderStatus(status_value)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "INVALID_STATUS",
                    "message": "status inválido para filtro.",
                    "status": status_value,
                },
            ) from exc
        query = query.filter(Order.status == status_enum)

    total = query.count()

    items = (
        query.order_by(Order.created_at.desc(), Order.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def _create_public_order_via_existing_flow(
    *,
    db: Session,
    payload: PublicCreateOrderRequest,
    guest_session_id: str,
    idempotency_key: str,
    device_fp: str,
    request: Request,
    # 🔥 ALTERAÇÃO: Adicionado parâmetro current_user com Depends
    # ERRO current_user: User = Depends(get_current_user),
    current_user: User,  # 🔥 ALTERAÇÃO: Remover Depends daqui, receber como parâmetro
) -> dict[str, Any]:
    _ = idempotency_key
    _ = device_fp
    _ = request

    create_payload = CreateOrderIn.model_validate(payload.model_dump())

    result = create_order_core(
        db=db,
        region=create_payload.region.value,
        sku_id=create_payload.sku_id,
        totem_id=create_payload.totem_id,
        desired_slot=create_payload.desired_slot,
        payment_method_value=create_payload.payment_method.value,
        card_type_value=create_payload.card_type.value if create_payload.card_type else None,
        amount_cents_input=create_payload.amount_cents,
        guest_phone=create_payload.customer_phone,
        user_id=current_user.id,  # 🔥 ALTERAÇÃO: Salvar ownership com user_id do usuário autenticado
    )

    order = result.order
    allocation = result.allocation

    public_access_token = _generate_public_access_token()

    # 🔥 ALTERAÇÃO: Garantir que o user_id está definido
    order.user_id = current_user.id  # Salvar ownership
    order.guest_session_id = guest_session_id
    order.public_access_token_hash = _hash_token(public_access_token)
    order.guest_phone = payload.customer_phone.strip() if payload.customer_phone else order.guest_phone
    order.consent_marketing = 1 if payload.consent_marketing else 0
    order.touch()

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "channel": order.channel.value,
        "status": order.status.value,
        "amount_cents": order.amount_cents,
        "payment_method": order.payment_method.value if order.payment_method else None,
        "allocation": {
            "allocation_id": allocation.id,
            "slot": allocation.slot,
            "ttl_sec": result.ttl_sec,
        },
        "public_access_token": public_access_token,
        "guest_session_id": guest_session_id,
        "user_id": order.user_id,  # 🔥 ALTERAÇÃO: Incluir user_id na resposta
    }


@router.post("/")
def create_public_order(
    payload: PublicCreateOrderRequest,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    device_fp: str = Header(..., alias="X-Device-Fingerprint"),
    current_user: User = Depends(get_current_user),  # 🔥 ALTERAÇÃO: Usar get_current_user do auth_dep
):
    # 🔥 ALTERAÇÃO: Verificar se o usuário está autenticado
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "AUTHENTICATION_REQUIRED",
                "message": "É necessário estar autenticado para criar pedidos.",
            },
        )

    guest_session_id = _resolve_guest_session_id(device_fp)

    if not guest_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "DEVICE_FINGERPRINT_REQUIRED",
                "message": "X-Device-Fingerprint é obrigatório.",
            },
        )

    if not str(idempotency_key or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "IDEMPOTENCY_KEY_REQUIRED",
                "message": "Idempotency-Key é obrigatório.",
            },
        )

    return _create_public_order_via_existing_flow(
        db=db,
        payload=payload,
        guest_session_id=guest_session_id,
        idempotency_key=idempotency_key,
        device_fp=device_fp,
        request=request,
        current_user=current_user,  # 🔥 ALTERAÇÃO: Passar current_user para a função
    )


@router.get("/")
def list_my_public_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_value: str | None = Query(default=None, alias="status"),
    current_user: User | None = Depends(get_current_public_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="X-Device-Fingerprint"),
):
    guest_session_id = _resolve_guest_session_id(device_fp)

    items, total = _list_orders_for_public_access(
        db=db,
        current_user=current_user,
        guest_session_id=guest_session_id,
        limit=limit,
        offset=offset,
        status_value=status_value,
    )

    order_ids = [order.id for order in items]
    fiscal_docs = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id.in_(order_ids))
        .all()
        if order_ids
        else []
    )
    fiscal_by_order_id = {doc.order_id: doc for doc in fiscal_docs}

    return {
        "items": [
            _serialize_order(order, fiscal=fiscal_by_order_id.get(order.id))
            for order in items
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        "filters": {
            "status": status_value,
        },
        "access_mode": {
            "user_id": current_user.id if current_user else None,
            "guest_session_id": guest_session_id,
        },
    }


@router.get("/{order_id}")
def get_my_public_order(
    order_id: str,
    current_user: User | None = Depends(get_current_public_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="X-Device-Fingerprint"),
    public_token_query: str | None = Query(default=None, alias="token"),
    public_token_header: str | None = Header(default=None, alias="X-Public-Access-Token"),
):
    guest_session_id = _resolve_guest_session_id(device_fp)
    public_token = public_token_header or public_token_query

    order = _get_order_for_public_access(
        db=db,
        order_id=order_id,
        current_user=current_user,
        guest_session_id=guest_session_id,
        public_token=public_token,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Pedido público não encontrado para este contexto de acesso.",
                "order_id": order_id,
                "guest_session_id": guest_session_id,
                "user_id": current_user.id if current_user else None,
                "public_token_present": bool(public_token),
            },
        )

    # 🔐 GET ORDER (CRÍTICO) - Verificar ownership
    # Se o usuário está autenticado, garantir que o pedido pertence a ele
    if current_user and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Pedido não encontrado",
                "order_id": order_id,
                "user_id": current_user.id,
                "order_user_id": order.user_id,
            },
        )

    fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )

    return _serialize_order(order, fiscal=fiscal)