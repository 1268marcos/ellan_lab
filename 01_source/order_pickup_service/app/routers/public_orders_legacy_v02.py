# 01_source/order_pickup_service/app/routers/public_orders.py
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument
from app.models.order import Order, OrderStatus
from app.models.user import User

router = APIRouter(prefix="/public/orders", tags=["public-orders"])


# =========================================================
# SERIALIZAÇÃO
# =========================================================

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
    }

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# =========================================================
# PAYLOAD PÚBLICO
# =========================================================

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


# =========================================================
# RESOLUÇÃO DE ACESSO
# =========================================================

def _resolve_guest_session_id(device_fp: str | None) -> str | None:
    value = str(device_fp or "").strip()
    return value or None



def _get_order_for_public_access(
    *,
    db: Session,
    order_id: str,
    current_user: User | None,
    guest_session_id: str | None,
    public_token: str | None = None,
) -> Order | None:
    query = db.query(Order).filter(Order.id == order_id)

    # 1. usuário autenticado
    if current_user is not None:
        order = query.filter(Order.user_id == current_user.id).first()
        if order:
            return order

    # 2. guest por fingerprint (SEU MODELO ATUAL)
    if guest_session_id:
        order = query.filter(Order.guest_session_id == guest_session_id).first()
        if order:
            return order

    # 3. NOVO: token público
    if public_token:
        token_hash = _hash_token(public_token)
        order = query.filter(Order.public_access_token_hash == token_hash).first()
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


# =========================================================
# INTEGRAÇÃO COM O FLOW EXISTENTE
# =========================================================

def _create_public_order_via_existing_flow(
    *,
    db: Session,
    payload: PublicCreateOrderRequest,
    guest_session_id: str,
    idempotency_key: str,
    device_fp: str,
    request: Request,
) -> dict[str, Any]:
    """
    PONTO ÚNICO DE INTEGRAÇÃO.

    ESTE MÉTODO DEVE CHAMAR O MESMO CORE JÁ USADO PELO ENDPOINT PROTEGIDO /orders.

    Motivo:
    - a criação real do pedido já existe e funciona;
    - nela estão as regras de:
      * slot-first
      * alocação da gaveta
      * idempotência real
      * criação do pedido ONLINE
      * consistência transacional
      * possíveis eventos/domínio/pickup associados

    Não reescrevi esse fluxo aqui para não quebrar arquitetura nem duplicar regra.

    IMPLEMENTAÇÃO ESPERADA:
    - importar a função/service já usado no router protegido
    - passar channel="ONLINE"
    - passar guest_session_id=device_fp
    - passar idempotency_key/device_fp
    - retornar o mesmo shape já devolvido por /orders
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "PUBLIC_CREATE_ORDER_INTEGRATION_PENDING",
            "message": (
                "A rota pública foi aberta, mas falta ligar este endpoint ao mesmo "
                "service/core já usado pelo endpoint protegido /orders."
            ),
            "next_required_file": (
                "Envie o arquivo do endpoint protegido de criação (/orders) "
                "ou o service/função que ele usa para criar pedido."
            ),
            "expected_contract": {
                "payload": payload.model_dump(),
                "guest_session_id": guest_session_id,
                "idempotency_key": idempotency_key,
                "device_fp": device_fp,
                "channel": "ONLINE",
            },
        },
    )


# =========================================================
# CRIAÇÃO PÚBLICA
# =========================================================

@router.post("/")
def create_public_order(
    payload: PublicCreateOrderRequest,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Chave de idempotência para evitar duplicação de pedidos Idempotency-Key"),
    device_fp: str = Header(..., alias="Identificador único do dispositivo para rastrear sessão de convidado X-Device-Fingerprint"),
):
    """
    Criar Pedido Público
    
    Arquivo: # 01_source/order_pickup_service/app/routers/public_orders.py

    Funcionalidade: def create_public_order(

    Endpoint: POST /public/orders/
    
    Descrição: Cria um novo pedido para usuários não autenticados (modo convidado). Este endpoint utiliza um fluxo de criação existente do sistema, garantindo regras de negócio como validação de slot, alocação de gaveta e idempotência.

    Respostas:
    - Código	Descrição
    - 200	Pedido criado com sucesso
    - 400	X-Device-Fingerprint ou Idempotency-Key ausente/inválido
    - 501	Integração com fluxo existente não implementada

    """
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
    )


# =========================================================
# LISTAGEM PÚBLICA
# =========================================================

@router.get("/")
def list_my_public_orders(
    limit: int = Query(default=20, ge=1, le=100, alias="Número máximo de itens"),
    offset: int = Query(default=0, ge=0, alias="Deslocamento para paginação offset"),
    status_value: str | None = Query(default=None, alias="Filtra por status do pedido"),
    current_user: User | None = Depends(get_current_public_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="Identificador do dispositivo para modo convidado X-Device-Fingerprint"),
):
    """
    Listar Meus Pedidos Públicos
    
    Arquivo: # 01_source/order_pickup_service/app/routers/public_orders.py

    Funcionalidade: def list_my_public_orders(

    Endpoint: GET /public/orders/
    
    Descrição: Lista os pedidos acessíveis ao contexto atual (usuário autenticado ou sessão convidada). Permite filtragem por status e paginação.

    Autenticação:
    - Pode ser autenticado (token JWT público) OU
    - Pode ser convidado via X-Device-Fingerprint

    Códigos de Resposta:
    - Código	Descrição
    - 200	Lista retornada com sucesso
    - 400	Status de filtro inválido
    - 401	Nenhuma forma de autenticação fornecida

    """
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


# =========================================================
# DETALHE PÚBLICO
# =========================================================

@router.get("/{order_id}")
def get_my_public_order(
    order_id: str,
    current_user: User | None = Depends(get_current_public_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="Identificador do dispositivo para modo convidado X-Device-Fingerprint"),
    public_token: str | None = Query(default=None, alias="token"),
):
    """
    Obter Detalhes de um Pedido Público

    Arquivo: # 01_source/order_pickup_service/app/routers/public_orders.py

    Funcionalidade: def get_my_public_order(

    Endpoint: GET /public/orders/{order_id}

    Descrição: Recupera os detalhes completos de um pedido específico, desde que seja acessível pelo contexto atual (usuário autenticado ou sessão convidada). Inclui informações fiscais quando disponíveis.

    Autenticação:
    - Pode ser autenticado (token JWT público) OU
    - Pode ser convidado via X-Device-Fingerprint

    Códigos de Resposta:
    - Código	Descrição
    - 200	Pedido encontrado e retornado
    - 404	Pedido não encontrado para o contexto de acesso

    Regras de Acesso:
    1. Modo Autenticado: Usuário com token JWT público válido acessa apenas seus próprios pedidos
    2. Modo Convidado: Usuário não autenticado acessa pedidos associados ao X-Device-Fingerprint
    3. Prioridade: Quando ambos estão presentes, o sistema retorna pedidos que correspondem a qualquer um dos contextos

    """
    guest_session_id = _resolve_guest_session_id(device_fp)

    order = _get_order_for_public_access(
        db=db,
        order_id=order_id,
        current_user=current_user,
        guest_session_id=guest_session_id,
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
            },
        )

    fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )

    return _serialize_order(order, fiscal=fiscal)

    