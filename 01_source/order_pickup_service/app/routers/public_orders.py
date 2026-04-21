# 01_source/order_pickup_service/app/routers/public_orders.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# 11/04/2026 - substituição de: Converte payload para CreateOrderIn 
#                         para: USAR PAYLOAD DIRETO (SEM CreateOrderIn)
# 14/04/2026 - Volta para produção desta versão do código
#              veja public_orders_BUGADA_POREM.py (causou problemas em ONLINE, porém, KIOSK ok)
#
# 17/04/2026 - nova def _serialize_order() e inclusão em @router.get("/{order_id}")
# 17/04/2026 - correção de "manual_code": 
# 17/04/2026 - patch para exibir o token de Código manual: token:5b0be4 para 886137
# 17/04/2026 - correção de "picked_up_at": em _serialize_order()
# 17/04/2026 - manual_code criptografado/cifrado
# 18/04/2026 - melhoramento payload - endereço - def _load_locker_snapshot()
# 19/04/2026 - datatime padrao ISO 8601
# 21/04/2026 - nova implementação para def _serialize_order()


from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, List, Dict
import hashlib
import secrets
import logging

import os
import base64

from app.core.datetime_utils import to_iso_utc

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user, get_current_user
from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument
from app.models.order import Order, OrderStatus, PaymentMethod, OrderChannel
from app.models.user import User
from app.schemas.orders import CreateOrderIn, OnlineRegion, OnlinePaymentMethod
from app.services.order_creation_service import create_order_core, CreateOrderCoreResult

# ==================== Importações adicionais ====================
from app.models.allocation import Allocation

from app.services.payment_resolution_service import resolve_payment_ui_code


from app.models.pickup import Pickup
from app.models.pickup_token import PickupToken
from app.services.pickup_qr_service import build_public_pickup_qr_value

from sqlalchemy import text

from app.services import backend_client



# Configuração de logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/orders", tags=["public-orders"])


# ==================== Funções Utilitárias / HELPERS ====================

from datetime import datetime, timezone

def _dt_iso(value: datetime | None) -> str | None:
    return to_iso_utc(value)


def _load_locker_snapshot_legacy_sem_endereco(
    db: Session,
    *,
    order: Order,
    allocation: Allocation | None = None,
    pickup: Pickup | None = None,
) -> dict[str, Any] | None:
    """
    Enriquecimento UX/CX:
    resolve dados amigáveis do locker para exibição no detalhe do pedido.
    Prioriza external_id = totem_id/locker_id.
    """
    candidate_locker_id = None

    if pickup and getattr(pickup, "locker_id", None):
        candidate_locker_id = str(pickup.locker_id).strip()
    elif allocation and getattr(allocation, "locker_id", None):
        candidate_locker_id = str(allocation.locker_id).strip()
    elif getattr(order, "totem_id", None):
        candidate_locker_id = str(order.totem_id).strip()

    if not candidate_locker_id:
        return None

    row = db.execute(
        text(
            """
            SELECT
                external_id,
                display_name,
                address_line,
                address_number,
                address_extra,
                district,
                city,
                state,
                postal_code,
                country
            FROM public.lockers
            WHERE external_id = :locker_id
              AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"locker_id": candidate_locker_id},
    ).mappings().first()

    if not row:
        return {
            "locker_id": candidate_locker_id,
            "display_name": candidate_locker_id,
            "address_line": None,
            "address_number": None,
            "address_extra": None,
            "district": None,
            "city": None,
            "state": None,
            "postal_code": None,
            "country": None,
        }

    return {
        "locker_id": row.get("external_id") or candidate_locker_id,
        "display_name": row.get("display_name") or candidate_locker_id,
        "address_line": row.get("address_line"),
        "address_number": row.get("address_number"),
        "address_extra": row.get("address_extra"),
        "district": row.get("district"),
        "city": row.get("city"),
        "state": row.get("state"),
        "postal_code": row.get("postal_code"),
        "country": row.get("country"),
    }


def _load_locker_snapshot(
    db: Session,
    *,
    order: Order,
    allocation: Allocation | None = None,
    pickup: Pickup | None = None,
) -> dict[str, Any] | None:
    candidate_locker_id = None

    if pickup and getattr(pickup, "locker_id", None):
        candidate_locker_id = str(pickup.locker_id).strip()
    elif allocation and getattr(allocation, "locker_id", None):
        candidate_locker_id = str(allocation.locker_id).strip()
    elif getattr(order, "totem_id", None):
        candidate_locker_id = str(order.totem_id).strip()

    if not candidate_locker_id:
        return None

    # 1) Fonte principal: registry/runtime, mesmo padrão rico usado pelo catálogo
    try:
        locker = backend_client.get_locker_registry_item(candidate_locker_id)
    except Exception:
        locker = None

    if locker:
        address = locker.get("address") if isinstance(locker.get("address"), dict) else {}

        return {
            "locker_id": (
                locker.get("locker_id")
                or locker.get("id")
                or locker.get("machine_id")
                or candidate_locker_id
            ),
            "display_name": (
                locker.get("display_name")
                or locker.get("locker_name")
                or locker.get("label")
                or candidate_locker_id
            ),
            "address_line": (
                address.get("address")
                or address.get("address_line")
                or locker.get("address_line")
                or locker.get("address")
            ),
            "address_number": (
                address.get("number")
                or address.get("address_number")
                or locker.get("address_number")
                or locker.get("number")
            ),
            "address_extra": (
                address.get("additional_information")
                or address.get("address_extra")
                or locker.get("address_extra")
                or locker.get("additional_information")
            ),
            "district": (
                address.get("locality")
                or address.get("district")
                or locker.get("district")
                or locker.get("locality")
            ),
            "city": address.get("city") or locker.get("city"),
            "state": (
                address.get("federative_unit")
                or address.get("state")
                or locker.get("state")
                or locker.get("federative_unit")
            ),
            "postal_code": address.get("postal_code") or locker.get("postal_code"),
            "country": address.get("country") or locker.get("country"),
        }

    # 2) Fallback: tabela local public.lockers
    row = db.execute(
        text(
            """
            SELECT
                external_id,
                display_name,
                address_line,
                address_number,
                address_extra,
                district,
                city,
                state,
                postal_code,
                country
            FROM public.lockers
            WHERE (
                external_id = :locker_id
                OR id = :locker_id
                OR machine_id = :locker_id
            )
              AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"locker_id": candidate_locker_id},
    ).mappings().first()

    if not row:
        return {
            "locker_id": candidate_locker_id,
            "display_name": candidate_locker_id,
            "address_line": None,
            "address_number": None,
            "address_extra": None,
            "district": None,
            "city": None,
            "state": None,
            "postal_code": None,
            "country": None,
        }

    return {
        "locker_id": row.get("external_id") or candidate_locker_id,
        "display_name": row.get("display_name") or candidate_locker_id,
        "address_line": row.get("address_line"),
        "address_number": row.get("address_number"),
        "address_extra": row.get("address_extra"),
        "district": row.get("district"),
        "city": row.get("city"),
        "state": row.get("state"),
        "postal_code": row.get("postal_code"),
        "country": row.get("country"),
    }









def _get_manual_code_aes_key() -> bytes:
    raw = str(os.getenv("MANUAL_CODE_AES_KEY", "")).strip()
    if not raw:
        raise RuntimeError(
            "MANUAL_CODE_AES_KEY não configurada. "
            "Use uma chave base64 urlsafe de 16, 24 ou 32 bytes."
        )

    padded = raw + "=" * (-len(raw) % 4)

    try:
        key = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception as exc:
        raise RuntimeError("MANUAL_CODE_AES_KEY inválida (base64 urlsafe).") from exc

    if len(key) not in {16, 24, 32}:
        raise RuntimeError(
            "MANUAL_CODE_AES_KEY deve decodificar para 16, 24 ou 32 bytes."
        )

    return key


def _build_manual_code_aad(*, pickup_id: str | None = None) -> bytes | None:
    if not pickup_id:
        return None
    return f"pickup={pickup_id}".encode("utf-8")


def _decrypt_manual_code(
    encrypted: str | None,
    *,
    pickup_id: str | None = None,
) -> str | None:
    if not encrypted:
        return None

    try:
        if not encrypted.startswith("v1:"):
            return None

        encoded = encrypted[3:]
        padded = encoded + "=" * (-len(encoded) % 4)
        blob = base64.urlsafe_b64decode(padded.encode("utf-8"))

        if len(blob) < 13:
            return None

        nonce = blob[:12]
        ciphertext = blob[12:]

        aesgcm = AESGCM(_get_manual_code_aes_key())
        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext,
            _build_manual_code_aad(pickup_id=pickup_id),
        )
        return plaintext.decode("utf-8")
    except Exception:
        logger.exception("MANUAL_CODE_DECRYPT_FAILED")
        return None


def _resolve_token_manual_code(token: PickupToken | None) -> str | None:
    if not token:
        return None

    decrypted = _decrypt_manual_code(
        getattr(token, "manual_code_encrypted", None),
        pickup_id=getattr(token, "pickup_id", None),
    )
    if decrypted:
        return decrypted

    legacy = getattr(token, "manual_code", None)
    if legacy:
        return legacy

    return None





def _serialize_order_legacy_falha_conteudo(order: Order, fiscal: FiscalDocument | None = None) -> dict[str, Any]:
    """Serializa pedido para resposta da API"""
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
        "customer_phone": order.guest_phone,
        # "customer_email": getattr(order, "customer_email", None),
        "guest_email": getattr(order, "guest_email", None),
    }


def _serialize_order_legacy_manual_code_texto_plano(
    order: Order,
    fiscal: FiscalDocument | None = None,
    *,
    pickup: Pickup | None = None,
    token: PickupToken | None = None,
    allocation: Allocation | None = None,
) -> dict[str, Any]:
    """Serializa pedido para resposta da API"""

    slot_value = None
    if getattr(order, "slot", None) is not None:
        slot_value = order.slot
    elif pickup and getattr(pickup, "slot", None) is not None:
        slot_value = pickup.slot
    elif allocation and getattr(allocation, "slot", None) is not None:
        slot_value = allocation.slot

    # expires_at_value = None
    # if pickup and getattr(pickup, "expires_at", None):
    #     expires_at_value = _dt_iso(pickup.expires_at)
    # elif token and getattr(token, "expires_at", None):
    #     expires_at_value = _dt_iso(token.expires_at)
    # 
    # qr_payload = None
    # if order and token and token.id and expires_at_value:
    #     qr_payload = build_public_pickup_qr_value(
    #         order_id=order.id,
    #         token_id=token.id,
    #         expires_at_iso=expires_at_value,
    #     )

    # 🔥 expires_at com fallback seguro e padronizado via _dt_iso()
    # Prioriza pickup > token, garantindo que o valor seja sempre string ISO ou None
    expires_at_value = (
        _dt_iso(getattr(pickup, "expires_at", None))
        or _dt_iso(getattr(token, "expires_at", None))
    )

    # QR payload depende do expires_at formatado
    qr_payload = None
    if order and token and token.id and expires_at_value:
        qr_payload = build_public_pickup_qr_value(
            order_id=order.id,
            token_id=token.id,
            expires_at_iso=expires_at_value,
        )


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
        # "picked_up_at": _dt_iso(order.picked_up_at),
        "picked_up_at": (
            _dt_iso(order.picked_up_at)
            or _dt_iso(getattr(pickup, "redeemed_at", None))
            or _dt_iso(getattr(pickup, "item_removed_at", None))
            or _dt_iso(getattr(pickup, "door_closed_at", None))
        ),
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
        "customer_phone": order.guest_phone,
        "guest_email": getattr(order, "guest_email", None),

        # 🔥 BLOCO NOVO PARA DETALHE DO PICKUP
        "allocation_id": getattr(order, "allocation_id", None) or (allocation.id if allocation else None),
        "slot": slot_value,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup.status.value if pickup and pickup.status else None,
        "pickup_lifecycle_stage": (
            pickup.lifecycle_stage.value
            if pickup and getattr(pickup, "lifecycle_stage", None)
            else None
        ),
        "expires_at": expires_at_value,
        "token_id": token.id if token else None,
        # "manual_code": None,  # não existe código em claro persistido; não inventar
        "manual_code": getattr(token, "manual_code", None),
        "qr_payload": qr_payload,
    }



def _serialize_order_legacy_falha_devolve_sempre_manual_code(
    order: Order,
    fiscal: FiscalDocument | None = None,
    *,
    pickup: Pickup | None = None,
    token: PickupToken | None = None,
    allocation: Allocation | None = None,
    locker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serializa pedido para resposta da API"""

    slot_value = None
    if getattr(order, "slot", None) is not None:
        slot_value = order.slot
    elif pickup and getattr(pickup, "slot", None) is not None:
        slot_value = pickup.slot
    elif allocation and getattr(allocation, "slot", None) is not None:
        slot_value = allocation.slot

    expires_at_value = None
    if pickup and getattr(pickup, "expires_at", None):
        expires_at_value = _dt_iso(pickup.expires_at)
    elif token and getattr(token, "expires_at", None):
        expires_at_value = _dt_iso(token.expires_at)

    qr_payload = None
    if order and token and token.id and expires_at_value:
        qr_payload = build_public_pickup_qr_value(
            order_id=order.id,
            token_id=token.id,
            expires_at_iso=expires_at_value,
        )



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
        "pickup_deadline_at": (
            _dt_iso(order.pickup_deadline_at)
            or _dt_iso(getattr(pickup, "expires_at", None))
            or _dt_iso(getattr(token, "expires_at", None))
        ),
        "picked_up_at": (
            _dt_iso(order.picked_up_at)
            or _dt_iso(getattr(pickup, "redeemed_at", None))
            or _dt_iso(getattr(pickup, "item_removed_at", None))
            or _dt_iso(getattr(pickup, "door_closed_at", None))
        ),
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
        "customer_phone": order.guest_phone,
        "guest_email": getattr(order, "guest_email", None),

        "allocation_id": getattr(order, "allocation_id", None) or (allocation.id if allocation else None),
        "slot": slot_value,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup.status.value if pickup and pickup.status else None,
        "pickup_lifecycle_stage": (
            pickup.lifecycle_stage.value
            if pickup and getattr(pickup, "lifecycle_stage", None)
            else None
        ),
        # ✅ expires_at agora vem de cálculo com fallback + _dt_iso()
        "expires_at": expires_at_value, # ops
        "token_id": token.id if token else None,
        "manual_code": _resolve_token_manual_code(token),
        "qr_payload": qr_payload,
        "locker": locker,
    }


def _serialize_order_legacy_sem_credito50(
    order: Order,
    fiscal: FiscalDocument | None = None,
    *,
    pickup: Pickup | None = None,
    token: PickupToken | None = None,
    allocation: Allocation | None = None,
    locker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serializa pedido para resposta da API"""

    now = datetime.now(timezone.utc)

    slot_value = None
    if getattr(order, "slot", None) is not None:
        slot_value = order.slot
    elif pickup and getattr(pickup, "slot", None) is not None:
        slot_value = pickup.slot
    elif allocation and getattr(allocation, "slot", None) is not None:
        slot_value = allocation.slot

    expires_at_dt = None
    if pickup and getattr(pickup, "expires_at", None):
        expires_at_dt = pickup.expires_at
    elif token and getattr(token, "expires_at", None):
        expires_at_dt = token.expires_at

    if expires_at_dt and expires_at_dt.tzinfo is None:
        expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)

    expires_at_value = _dt_iso(expires_at_dt)

    status_value = order.status.value if order.status else None
    pickup_status_value = pickup.status.value if pickup and pickup.status else None

    expired_by_status = status_value in {"EXPIRED", "EXPIRED_CREDIT_50"}
    expired_by_pickup = pickup_status_value == "EXPIRED"
    expired_by_time = bool(expires_at_dt and now > expires_at_dt)

    hide_pickup_credentials = expired_by_status or expired_by_pickup or expired_by_time

    qr_payload = None
    if not hide_pickup_credentials and order and token and token.id and expires_at_value:
        qr_payload = build_public_pickup_qr_value(
            order_id=order.id,
            token_id=token.id,
            expires_at_iso=expires_at_value,
        )

    manual_code = None
    if not hide_pickup_credentials:
        manual_code = _resolve_token_manual_code(token)

    return {
        "id": order.id,
        "order_id": order.id,
        "user_id": order.user_id,
        "channel": order.channel.value if order.channel else None,
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": order.sku_id,
        "amount_cents": order.amount_cents,
        "status": status_value,
        "gateway_transaction_id": order.gateway_transaction_id,
        "payment_method": order.payment_method.value if order.payment_method else None,
        "payment_status": order.payment_status.value if order.payment_status else None,
        "card_type": order.card_type.value if order.card_type else None,
        "payment_updated_at": _dt_iso(order.payment_updated_at),
        "paid_at": _dt_iso(order.paid_at),
        "pickup_deadline_at": (
            _dt_iso(order.pickup_deadline_at)
            or _dt_iso(getattr(pickup, "expires_at", None))
            or _dt_iso(getattr(token, "expires_at", None))
        ),
        "picked_up_at": (
            _dt_iso(order.picked_up_at)
            or _dt_iso(getattr(pickup, "redeemed_at", None))
            or _dt_iso(getattr(pickup, "item_removed_at", None))
            or _dt_iso(getattr(pickup, "door_closed_at", None))
        ),
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
        "customer_phone": order.guest_phone,
        "guest_email": getattr(order, "guest_email", None),

        "allocation_id": getattr(order, "allocation_id", None) or (allocation.id if allocation else None),
        "slot": slot_value,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup_status_value,
        "pickup_lifecycle_stage": (
            pickup.lifecycle_stage.value
            if pickup and getattr(pickup, "lifecycle_stage", None)
            else None
        ),
        "expires_at": expires_at_value,
        "token_id": None if hide_pickup_credentials else (token.id if token else None),
        "manual_code": manual_code,
        "qr_payload": qr_payload,
        "locker": locker,
        "pickup_expired_effective": hide_pickup_credentials,
    }


def _serialize_order(
    order: Order,
    fiscal: FiscalDocument | None = None,
    *,
    pickup: Pickup | None = None,
    token: PickupToken | None = None,
    allocation: Allocation | None = None,
    locker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    slot_value = None
    if getattr(order, "slot", None) is not None:
        slot_value = order.slot
    elif pickup and getattr(pickup, "slot", None) is not None:
        slot_value = pickup.slot
    elif allocation and getattr(allocation, "slot", None) is not None:
        slot_value = allocation.slot

    expires_at_dt = None
    if pickup and getattr(pickup, "expires_at", None):
        expires_at_dt = pickup.expires_at
    elif token and getattr(token, "expires_at", None):
        expires_at_dt = token.expires_at
    elif getattr(order, "pickup_deadline_at", None):
        expires_at_dt = order.pickup_deadline_at

    if expires_at_dt and expires_at_dt.tzinfo is None:
        expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)

    expires_at_value = _dt_iso(expires_at_dt)

    status_value = order.status.value if order.status else None
    pickup_status_value = pickup.status.value if pickup and pickup.status else None

    expired_by_status = status_value in {"EXPIRED", "EXPIRED_CREDIT_50"}
    expired_by_pickup = pickup_status_value == "EXPIRED"
    expired_by_time = bool(expires_at_dt and now > expires_at_dt)

    hide_pickup_credentials = expired_by_status or expired_by_pickup or expired_by_time

    qr_payload = None
    if not hide_pickup_credentials and order and token and token.id and expires_at_value:
        qr_payload = build_public_pickup_qr_value(
            order_id=order.id,
            token_id=token.id,
            expires_at_iso=expires_at_value,
        )

    manual_code = None
    if not hide_pickup_credentials:
        manual_code = _resolve_token_manual_code(token)

    return {
        "id": order.id,
        "order_id": order.id,
        "user_id": order.user_id,
        "channel": order.channel.value if order.channel else None,
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": order.sku_id,
        "amount_cents": order.amount_cents,
        "status": status_value,
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
        "receipt_json_path": f"/public/fiscal/by-code/{fiscal.receipt_code}" if fiscal else None,
        "public_access_enabled": bool(getattr(order, "public_access_token_hash", None)),
        "customer_phone": order.guest_phone,
        "guest_email": getattr(order, "guest_email", None),
        "allocation_id": getattr(order, "allocation_id", None) or (allocation.id if allocation else None),
        "slot": slot_value,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup_status_value,
        "pickup_lifecycle_stage": (
            pickup.lifecycle_stage.value if pickup and getattr(pickup, "lifecycle_stage", None) else None
        ),
        "expires_at": expires_at_value,
        "token_id": None if hide_pickup_credentials else (token.id if token else None),
        "manual_code": manual_code,
        "qr_payload": qr_payload,
        "locker": locker,
        "pickup_expired_effective": hide_pickup_credentials,
    }



def _hash_token(token: str) -> str:
    """Gera hash SHA256 do token"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_public_access_token() -> tuple[str, str]:
    """Gera token de acesso público e seu hash"""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def _resolve_guest_session_id(device_fp: str | None) -> str | None:
    """Resolve guest session ID a partir do device fingerprint"""
    value = str(device_fp or "").strip()
    return value or None


def _validate_payment_method_for_region(
    payment_method: str, 
    region: str
) -> None:
    """Valida se o método de pagamento é compatível com a região"""
    # Mapeamento de métodos por região
    region_methods = {
        # Brasil
        "SP": {"pix", "boleto", "creditCard", "debitCard", "giftCard", 
               "apple_pay", "google_pay", "mercado_pago_wallet"},
        "RJ": {"pix", "boleto", "creditCard", "debitCard", "giftCard"},
        "MG": {"pix", "boleto", "creditCard", "debitCard", "giftCard"},
        "RS": {"pix", "boleto", "creditCard", "debitCard", "giftCard"},
        "BA": {"pix", "boleto", "creditCard", "debitCard", "giftCard"},
        
        # Portugal
        "PT": {"mbway", "multibanco_reference", "creditCard", "debitCard", 
               "giftCard", "apple_pay", "google_pay"},
        
        # México
        "MX": {"oxxo", "spei", "creditCard", "debitCard", "giftCard"},
        
        # Argentina
        "AR": {"rapipago", "pagofacil", "creditCard", "debitCard"},
        
        # China
        "CN": {"alipay", "wechat_pay", "unionpay", "creditCard", "debitCard"},
        
        # Japão
        "JP": {"paypay", "line_pay", "rakuten_pay", "konbini", "creditCard"},
        
        # Tailândia
        "TH": {"promptpay", "truemoney", "creditCard"},
        
        # Indonésia
        "ID": {"go_pay", "ovo", "dana", "creditCard"},
        
        # Singapura
        "SG": {"grabpay", "dbs_paylah", "creditCard"},
        
        # Filipinas
        "PH": {"gcash", "paymaya", "creditCard"},
        
        # Emirados Árabes
        "AE": {"tabby", "payby", "creditCard"},
        
        # Turquia
        "TR": {"troy", "bkm_express", "creditCard"},
        
        # Rússia
        "RU": {"mir", "yoomoney", "creditCard"},
        
        # Austrália
        "AU": {"afterpay", "zip", "bpay", "creditCard"},
        
        # África do Sul
        "ZA": {"yoco", "paystack", "creditCard"},
        
        # Quênia
        "KE": {"m_pesa", "airtel_money", "creditCard"},
        
        # Nigéria
        "NG": {"paystack", "flutterwave", "creditCard"},
    }
    
    # Extrai base da região (primeiros 2 caracteres para regiões compostas)
    region_base = region[:2] if len(region) >= 2 else region
    
    allowed_methods = region_methods.get(region, region_methods.get(region_base, set()))
    
    if allowed_methods and payment_method not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "PAYMENT_METHOD_NOT_ALLOWED_IN_REGION",
                "message": f"Método de pagamento {payment_method} não é suportado na região {region}",
                "region": region,
                "payment_method": payment_method,
                "allowed_methods": list(allowed_methods),
            },
        )


def _validate_amount_for_region(amount_cents: int, region: str) -> None:
    """Valida se o valor está dentro dos limites da região"""
    # Limites por região (em centavos)
    limits = {
        "BR": {"min": 1, "max": 500000},      # R$ 5.000
        "PT": {"min": 1, "max": 100000},      # € 1.000
        "MX": {"min": 1, "max": 200000},      # MX$ 2.000
        "CN": {"min": 1, "max": 1000000},     # ¥ 10.000
        "JP": {"min": 1, "max": 1000000},     # ¥ 10.000
        "US": {"min": 1, "max": 100000},      # $ 1.000
        "AE": {"min": 1, "max": 500000},      # AED 5.000
        "AU": {"min": 1, "max": 100000},      # AU$ 1.000
        "default": {"min": 1, "max": 100000},
    }
    
    region_base = region[:2] if len(region) >= 2 else region
    region_limits = limits.get(region_base, limits["default"])
    
    if amount_cents < region_limits["min"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "AMOUNT_BELOW_MINIMUM",
                "message": f"Valor mínimo para região {region} é {region_limits['min']} centavos",
                "min_amount": region_limits["min"],
                "amount_cents": amount_cents,
            },
        )
    
    if amount_cents > region_limits["max"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "AMOUNT_EXCEEDS_LIMIT",
                "message": f"Valor máximo para região {region} é {region_limits['max']} centavos",
                "max_amount": region_limits["max"],
                "amount_cents": amount_cents,
            },
        )


def _get_order_for_public_access(
    *,
    db: Session,
    order_id: str,
    current_user: User | None,
    guest_session_id: str | None,
    public_token: str | None,
) -> Order | None:
    """Recupera pedido para acesso público com diferentes métodos de autenticação"""
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
    region: str | None = None,
    payment_method: str | None = None,
) -> tuple[list[Order], int]:
    """Lista pedidos para acesso público com filtros"""
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
    
    if region:
        query = query.filter(Order.region == region)
    
    if payment_method:
        try:
            payment_method_enum = PaymentMethod(payment_method)
            query = query.filter(Order.payment_method == payment_method_enum)
        except ValueError:
            pass  # Ignora método inválido

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
    current_user: User,
) -> dict[str, Any]:
    """Cria pedido público utilizando o fluxo existente"""
    _ = idempotency_key
    _ = device_fp
    _ = request

    # Valida método de pagamento para a região
    _validate_payment_method_for_region(payload.payment_method, payload.region)
    
    # Valida valor para a região
    if payload.amount_cents:
        _validate_amount_for_region(payload.amount_cents, payload.region)

    # 🔥 USAR PAYLOAD DIRETO (SEM CreateOrderIn)
    # Chama core de criação
    result = create_order_core(
        db=db,
        region=payload.region,
        sku_id=payload.sku_id,
        totem_id=payload.totem_id,
        desired_slot=payload.desired_slot,
        payment_method_value=payload.payment_method,
        amount_cents_input=payload.amount_cents,
        guest_phone=payload.customer_phone,
        # customer_email=getattr(payload, "customer_email", None),
        guest_email=payload.guest_email,
        user_id=current_user.id,
        payment_interface=payload.payment_interface,
        wallet_provider=payload.wallet_provider,
        device_id=device_fp,
        ip_address=request.client.host if request.client else None,
    )

    order = result.order
    order.idempotency_key = idempotency_key
    allocation = result.allocation

    # Gera token de acesso público
    public_access_token, public_access_token_hash = _generate_public_access_token()

    # Atualiza pedido com informações adicionais
    order.user_id = current_user.id
    order.guest_session_id = guest_session_id
    order.public_access_token_hash = public_access_token_hash
    order.guest_phone = payload.customer_phone.strip() if payload.customer_phone else order.guest_phone
    order.consent_marketing = 1 if payload.consent_marketing else 0
    order.touch()

    db.add(order)
    db.commit()
    db.refresh(order)

    logger.info(
        f"Public order created - order_id={order.id}, "
        f"user_id={current_user.id}, region={payload.region}, "
        f"payment_method={payload.payment_method}, amount={order.amount_cents}"
    )

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
            "expires_at": _dt_iso(result.payment_timeout_at) if result.payment_timeout_at else None,
        },
        "public_access_token": public_access_token,
        "guest_session_id": guest_session_id,
        "user_id": order.user_id,
        "region": order.region,
    }


# ==================== Schemas ====================

class PublicCreateOrderRequest(BaseModel):
    """Request para criação de pedido público"""
    region: str = Field(..., min_length=2, max_length=8, description="Código da região")
    sku_id: str = Field(..., min_length=1, max_length=255)
    totem_id: str = Field(..., min_length=1, max_length=255)
    desired_slot: int = Field(..., ge=1, le=9999, description="Slot desejado")
    payment_method: str = Field(..., min_length=1, max_length=64)
    payment_interface: Optional[str] = Field(default=None, max_length=32)
    amount_cents: Optional[int] = Field(default=None, ge=1)
    customer_phone: Optional[str] = Field(default=None, max_length=64)
    # customer_email: Optional[str] = Field(default=None, max_length=255)
    guest_email: Optional[str] = Field(default=None, max_length=255)
    wallet_provider: Optional[str] = Field(default=None, max_length=64)
    consent_marketing: bool = False
    
    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        region_upper = v.strip().upper()
        valid_regions = {
            # América Latina
            "SP", "RJ", "MG", "RS", "BA", "BR", "MX", "AR", "CO", "CL", "PE",
            "EC", "UY", "PY", "BO", "VE", "CR", "PA", "DO",
            # América do Norte
            "US_NY", "US_CA", "US_TX", "US_FL", "US_IL", "CA_ON", "CA_QC", "CA_BC",
            # Europa
            "PT", "ES", "FR", "DE", "UK", "IT", "NL", "BE", "CH", "SE",
            "NO", "DK", "FI", "IE", "AT", "PL", "CZ", "GR", "HU", "RO", "RU", "TR",
            # África
            "ZA", "NG", "KE", "EG", "MA", "GH", "SN", "CI", "TZ", "UG", "RW", "MZ", "AO", "DZ", "TN",
            # Ásia
            "CN", "JP", "KR", "TH", "ID", "SG", "PH", "VN", "MY",
            # Oriente Médio
            "AE", "SA", "QA", "KW", "BH", "OM", "JO",
            # Oceania
            "AU", "NZ",
        }
        if region_upper not in valid_regions:
            raise ValueError(f"Região inválida: {v}")
        return region_upper
    
    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        valid_methods = {
            "pix", "boleto", "creditcard", "debitcard", "giftcard", "prepaidcard",
            "apple_pay", "google_pay", "samsung_pay", "mercado_pago_wallet",
            "mbway", "multibanco_reference", "sofort", "ideal", "bancontact",
            "alipay", "wechat_pay", "paypay", "line_pay", "rakuten_pay",
            "promptpay", "truemoney", "go_pay", "ovo", "dana", "grabpay",
            "gcash", "paymaya", "tabby", "afterpay", "zip", "m_pesa",
            "airtel_money", "mtn_money", "troy", "mir", "yoomoney",
        }
        # anteriormente foi creditCard agora creditcard (veja o conjunto acima)
        v_normalized = v.lower()

        # if v.lower() not in valid_methods:
        if v_normalized not in valid_methods:
            raise ValueError(f"Método de pagamento inválido: {v}")
        
        # return v.lower()
        return v_normalized


class PublicOrderListResponse(BaseModel):
    """Resposta para listagem de pedidos públicos"""
    items: List[Dict[str, Any]]
    pagination: Dict[str, int]
    filters: Dict[str, Any]
    access_mode: Dict[str, Any]


class PublicOrderCreateResponse(BaseModel):
    """Resposta para criação de pedido público"""
    order_id: str
    channel: str
    status: str
    amount_cents: int
    payment_method: Optional[str]
    allocation: Dict[str, Any]
    public_access_token: str
    guest_session_id: str
    user_id: str
    region: str


# ==================== Endpoints ====================

@router.post("/", response_model=PublicOrderCreateResponse)
def create_public_order(
    payload: PublicCreateOrderRequest,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    device_fp: str = Header(..., alias="X-Device-Fingerprint"),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo pedido público.
    
    Requer:
    - Autenticação do usuário
    - Idempotency-Key header
    - X-Device-Fingerprint header
    """
    # Verifica autenticação
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "AUTHENTICATION_REQUIRED",
                "message": "É necessário estar autenticado para criar pedidos.",
            },
        )

    # Valida device fingerprint
    guest_session_id = _resolve_guest_session_id(device_fp)
    if not guest_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "DEVICE_FINGERPRINT_REQUIRED",
                "message": "X-Device-Fingerprint é obrigatório.",
            },
        )

    # ===============================
    # NORMALIZAÇÃO SEGURA (SEM MIDDLEWARE)
    # ===============================
    resolved = resolve_payment_ui_code(
        db=db,
        raw_payment_method=payload.payment_method,
        raw_payment_interface=payload.payment_interface,
        raw_wallet_provider=payload.wallet_provider,
    )

    payload.payment_method = resolved.get("payment_method")
    payload.payment_interface = resolved.get("payment_interface")
    payload.wallet_provider = resolved.get("wallet_provider")



    # Valida idempotency key
    if not str(idempotency_key or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "IDEMPOTENCY_KEY_REQUIRED",
                "message": "Idempotency-Key é obrigatório.",
            },
        )

    # Verifica duplicata por idempotency key
    existing_order = db.query(Order).filter(
        Order.idempotency_key == idempotency_key
    ).first()
    
    if existing_order:
        logger.info(f"Idempotency key hit: {idempotency_key}")
        # Retorna pedido existente
        allocation = db.query(Allocation).filter(
            Allocation.order_id == existing_order.id
        ).first()
        
        return {
            "order_id": existing_order.id,
            "channel": existing_order.channel.value,
            "status": existing_order.status.value,
            "amount_cents": existing_order.amount_cents,
            "payment_method": existing_order.payment_method.value if existing_order.payment_method else None,
            "allocation": {
                "allocation_id": allocation.id if allocation else None,
                "slot": allocation.slot if allocation else None,
                "ttl_sec": None,
            },
            "public_access_token": None,
            "guest_session_id": existing_order.guest_session_id,
            "user_id": existing_order.user_id,
            "region": existing_order.region,
        }

    return _create_public_order_via_existing_flow(
        db=db,
        payload=payload,
        guest_session_id=guest_session_id,
        idempotency_key=idempotency_key,
        device_fp=device_fp,
        request=request,
        current_user=current_user,
    )


@router.get("/")
def list_my_public_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_value: str | None = Query(default=None, alias="status"),
    region: str | None = Query(default=None, description="Filtrar por região"),
    payment_method: str | None = Query(default=None, description="Filtrar por método de pagamento"),
    current_user: User | None = Depends(get_current_public_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="X-Device-Fingerprint"),
):
    """
    Lista pedidos públicos do usuário atual.
    
    Suporta:
    - Autenticação por usuário
    - Autenticação por guest session (X-Device-Fingerprint)
    - Filtros por status, região e método de pagamento
    """
    guest_session_id = _resolve_guest_session_id(device_fp)

    items, total = _list_orders_for_public_access(
        db=db,
        current_user=current_user,
        guest_session_id=guest_session_id,
        limit=limit,
        offset=offset,
        status_value=status_value,
        region=region,
        payment_method=payment_method,
    )

    # Busca documentos fiscais
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
            "has_next": offset + limit < total,
            "has_prev": offset > 0,
        },
        "filters": {
            "status": status_value,
            "region": region,
            "payment_method": payment_method,
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
    """
    Obtém detalhes de um pedido público específico.
    
    Suporta acesso via:
    - Usuário autenticado (owner)
    - Guest session (X-Device-Fingerprint)
    - Token público (query ou header)
    """
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

    # Verificação de ownership adicional para usuário autenticado
    if current_user and order.user_id and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Pedido não encontrado",
                "order_id": order_id,
            },
        )

    # Busca documento fiscal
    # fiscal = (
    #     db.query(FiscalDocument)
    #     .filter(FiscalDocument.order_id == order.id)
    #     .first()
    # )
    # 
    # return _serialize_order(order, fiscal=fiscal)
    # Busca documento fiscal
    fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )

    # Busca allocation associada
    allocation = None
    if getattr(order, "allocation_id", None):
        allocation = (
            db.query(Allocation)
            .filter(Allocation.id == order.allocation_id)
            .first()
        )

    if allocation is None:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order.id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )

    # Busca pickup mais recente
    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )

    # Busca token atual/mais recente
    token = None
    if pickup and getattr(pickup, "current_token_id", None):
        token = (
            db.query(PickupToken)
            .filter(PickupToken.id == pickup.current_token_id)
            .first()
        )

    if token is None and pickup:
        token = (
            db.query(PickupToken)
            .filter(PickupToken.pickup_id == pickup.id)
            .order_by(PickupToken.expires_at.desc(), PickupToken.id.desc())
            .first()
        )


    locker = _load_locker_snapshot(
        db,
        order=order,
        allocation=allocation,
        pickup=pickup,
    )

    return _serialize_order(
        order,
        fiscal=fiscal,
        pickup=pickup,
        token=token,
        allocation=allocation,
        locker=locker,
    )






@router.post("/{order_id}/cancel")
def cancel_public_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    device_fp: str | None = Header(default=None, alias="X-Device-Fingerprint"),
):
    """
    Cancela um pedido público.
    
    Apenas o owner do pedido pode cancelar.
    """
    guest_session_id = _resolve_guest_session_id(device_fp)
    
    # Busca pedido
    order = _get_order_for_public_access(
        db=db,
        order_id=order_id,
        current_user=current_user,
        guest_session_id=guest_session_id,
        public_token=None,
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Pedido não encontrado",
            },
        )
    
    # Verifica ownership
    if current_user and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "CANCEL_NOT_ALLOWED",
                "message": "Você não tem permissão para cancelar este pedido",
            },
        )
    
    # Verifica se pode cancelar
    if order.status not in [OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "CANCEL_NOT_ALLOWED",
                "message": f"Pedido em status {order.status.value} não pode ser cancelado",
                "current_status": order.status.value,
            },
        )
    
    # Atualiza status
    order.status = OrderStatus.CANCELLED
    order.touch()
    db.commit()
    
    logger.info(f"Public order cancelled - order_id={order_id}, user_id={current_user.id}")
    
    return {
        "order_id": order.id,
        "status": order.status.value,
        "message": "Pedido cancelado com sucesso",
    }


