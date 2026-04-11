# 01_source/order_pickup_service/app/services/order_creation_service.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# 05/04/2026 - Resolvendo Hardcoded
# 05/04/2026 - Corrigido para usar capability profile do banco como source of truth
# 06/04/2026 - Ajuste order_creation_service

from __future__ import annotations

import logging
import re
import uuid
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.lifecycle_client import LifecycleClientError
# from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus, PaymentMethod
from app.services import backend_client
from app.services.lifecycle_integration import register_prepayment_timeout_deadline
from app.services.locker_service import validate_locker_for_order
from app.services.payment_capability_service import get_payment_capabilities

from app.services.payment_resolution_service import resolve_payment_ui_code

from app.services.capability_constraint_service import get_capability_constraint


# ==================== Constantes e Patterns ====================

# Padrões de locker_id expandidos para mercados globais
LOCKER_ID_PATTERNS = {
    # Brasil
    "BR": re.compile(r"^([A-Z]{2})-[A-Z0-9]+(?:-[A-Z0-9]+)*-LK-\d{3}$"),
    # Portugal
    "PT": re.compile(r"^([A-Z]{2})-[A-Z0-9]+(?:-[A-Z0-9]+)*-LK-\d{3}$"),
    # México
    "MX": re.compile(r"^MX-[A-Z0-9]+-LK-\d{3}$"),
    # Argentina
    "AR": re.compile(r"^AR-[A-Z0-9]+-LK-\d{3}$"),
    # Colômbia
    "CO": re.compile(r"^CO-[A-Z0-9]+-LK-\d{3}$"),
    # Chile
    "CL": re.compile(r"^CL-[A-Z0-9]+-LK-\d{3}$"),
    # China
    "CN": re.compile(r"^CN-[A-Z0-9]+-LK-\d{4}$"),
    # Japão
    "JP": re.compile(r"^JP-[A-Z0-9]+-LK-\d{3}$"),
    # Tailândia
    "TH": re.compile(r"^TH-[A-Z0-9]+-LK-\d{3}$"),
    # Indonésia
    "ID": re.compile(r"^ID-[A-Z0-9]+-LK-\d{3}$"),
    # Singapura
    "SG": re.compile(r"^SG-[A-Z0-9]+-LK-\d{3}$"),
    # Filipinas
    "PH": re.compile(r"^PH-[A-Z0-9]+-LK-\d{3}$"),
    # Emirados Árabes
    "AE": re.compile(r"^AE-[A-Z0-9]+-LK-\d{3}$"),
    # Turquia
    "TR": re.compile(r"^TR-[A-Z0-9]+-LK-\d{3}$"),
    # Rússia
    "RU": re.compile(r"^RU-[A-Z0-9]+-LK-\d{3}$"),
    # Austrália
    "AU": re.compile(r"^AU-[A-Z0-9]+-LK-\d{3}$"),
    # África do Sul
    "ZA": re.compile(r"^ZA-[A-Z0-9]+-LK-\d{3}$"),
    # Nigéria
    "NG": re.compile(r"^NG-[A-Z0-9]+-LK-\d{3}$"),
    # Quênia
    "KE": re.compile(r"^KE-[A-Z0-9]+-LK-\d{3}$"),
    # Desenvolvimento
    "DEV": re.compile(r"^CACIFO-([A-Z]{2})-\d{3}$"),
}

# Limites por região
REGION_LIMITS = {
    "BR": {"max_amount": 500000, "min_slot": 1, "max_slot": 999},
    "PT": {"max_amount": 100000, "min_slot": 1, "max_slot": 999},
    "MX": {"max_amount": 200000, "min_slot": 1, "max_slot": 999},
    "CN": {"max_amount": 1000000, "min_slot": 1, "max_slot": 9999},
    "JP": {"max_amount": 1000000, "min_slot": 1, "max_slot": 999},
    "US": {"max_amount": 100000, "min_slot": 1, "max_slot": 999},
    "default": {"max_amount": 100000, "min_slot": 1, "max_slot": 999},
}

ONLINE_CAPABILITY_CONTEXT_CANDIDATES = (
    "ORDER_CREATION",
    "ONLINE_ORDER_CREATION",
    "ONLINE_CHECKOUT",
    "CHECKOUT",
)

logger = logging.getLogger(__name__)


@dataclass
class CreateOrderCoreResult:
    order: Order
    allocation: Allocation
    ttl_sec: int
    payment_timeout_at: Optional[datetime] = None


# ==================== Funções Utilitárias ====================

def normalize_upper_list(values: list[str] | None) -> list[str]:
    return [str(v).strip().upper() for v in (values or []) if str(v).strip()]


def get_region_base(region: str) -> str:
    """Extrai base da região (primeiros 2 caracteres)"""
    region_upper = str(region or "").upper()
    if region_upper.startswith("US_"):
        return "US"
    if region_upper.startswith("CA_"):
        return "CA"
    if len(region_upper) >= 2:
        return region_upper[:2]
    return region_upper


def resolve_online_prepayment_ttl_sec(
    *,
    db: Session,
    region: str,
    payment_method: str,
    amount_cents: Optional[int] = None,
) -> int:
    """Resolve TTL com base na região, método e valor"""
    # ttl_sec = resolve_prepayment_timeout_seconds(
    #     region_code=region,
    #     order_channel=OrderChannel.ONLINE.value,
    #     payment_method=payment_method,
    # )
    # talvez seja necessário corrigir para:
    # ttl_sec = capabilities["constraints"].get("prepayment_timeout_sec")
    # 01_source/order_pickup_service/app/routers/kiosk.py

    ttl_sec = get_capability_constraint(
        db=db,
        region=region,
        channel=OrderChannel.ONLINE.value,
        context="CHECKOUT",  # ou seu contexto correto
        code="prepayment_timeout_sec",
    )  

    
    # Ajuste baseado no valor para métodos específicos
    if amount_cents and payment_method in {"boleto", "bank_transfer"}:
        if amount_cents >= 50000:
            ttl_sec = max(ttl_sec, 48 * 60 * 60)
        elif amount_cents >= 10000:
            ttl_sec = max(ttl_sec, 24 * 60 * 60)

    if int(ttl_sec) <= 0:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "ONLINE_PAYMENT_TTL_POLICY_INVALID",
                "message": "O TTL configurado deve ser maior que zero.",
                "region": region,
                "channel": OrderChannel.ONLINE.value,
                "payment_method": payment_method,
                "ttl_value": ttl_sec,
            },
        )

    return int(ttl_sec)


def validate_locker_id_format(locker_id: str, region: Optional[str] = None) -> str:
    """Valida formato do locker_id para diferentes regiões"""
    raw = str(locker_id or "").strip().upper()

    if not raw:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_LOCKER_ID",
                "message": "locker_id não informado.",
            },
        )

    if LOCKER_ID_PATTERNS["DEV"].match(raw):
        return raw

    if region:
        region_base = get_region_base(region)
        if region_base in LOCKER_ID_PATTERNS and LOCKER_ID_PATTERNS[region_base].match(raw):
            return raw

    for _, pattern in LOCKER_ID_PATTERNS.items():
        if pattern.match(raw):
            return raw

    raise HTTPException(
        status_code=400,
        detail={
            "type": "INVALID_LOCKER_ID_FORMAT",
            "message": f"Formato inválido de locker_id para região {region}: {raw}",
            "expected_formats": list(LOCKER_ID_PATTERNS.keys()),
        },
    )


def _extract_pricing_amount_cents(pricing: dict) -> int:
    """Extrai valor do pricing com validação"""
    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")

    if amount_cents is None:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_RESPONSE",
                "message": "pricing missing amount_cents/price_cents",
            },
        )

    try:
        normalized = int(amount_cents)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_AMOUNT",
                "message": "pricing amount is invalid",
                "amount_cents": amount_cents,
            },
        ) from exc

    if normalized <= 0:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "PRICING_INVALID_AMOUNT",
                "message": "pricing amount must be > 0",
                "amount_cents": normalized,
            },
        )

    return normalized


def validate_amount_for_region(amount_cents: int, region: str) -> None:
    """Valida se o valor está dentro dos limites da região"""
    region_base = get_region_base(region)
    limits = REGION_LIMITS.get(region_base, REGION_LIMITS["default"])

    if amount_cents > limits["max_amount"]:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "AMOUNT_EXCEEDS_LIMIT",
                "message": f"Valor excede o limite máximo para a região {region}",
                "max_amount": limits["max_amount"],
                "amount_cents": amount_cents,
            },
        )


def validate_slot_for_region(slot: int, region: str) -> None:
    """Valida se o slot está dentro dos limites da região"""
    region_base = get_region_base(region)
    limits = REGION_LIMITS.get(region_base, REGION_LIMITS["default"])

    if slot < limits["min_slot"] or slot > limits["max_slot"]:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_SLOT_FOR_REGION",
                "message": f"Slot {slot} inválido para região {region}",
                "min_slot": limits["min_slot"],
                "max_slot": limits["max_slot"],
            },
        )


def compensate_failed_online_creation(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
) -> None:
    """Compensação em caso de falha na criação do pedido"""
    release_error: Exception | None = None

    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
    except Exception as exc:
        release_error = exc
        logger.exception(
            "online_order_compensation_release_failed - order_id=%s, allocation_id=%s",
            order.id,
            allocation.id,
        )

    try:
        db.delete(allocation)
        db.delete(order)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "online_order_compensation_db_failed - order_id=%s, allocation_id=%s",
            order.id,
            allocation.id,
        )
        raise

    if release_error is not None:
        raise release_error


def _get_online_capabilities(
    *,
    db: Session,
    region: str,
) -> dict:
    for context_code in ONLINE_CAPABILITY_CONTEXT_CANDIDATES:
        capabilities = get_payment_capabilities(
            db=db,
            region=region,
            channel=OrderChannel.ONLINE.value,
            context=context_code,
        )
        if capabilities.get("found"):
            return capabilities

    raise HTTPException(
        status_code=400,
        detail={
            "type": "PAYMENT_CAPABILITY_PROFILE_NOT_FOUND",
            "message": (
                "Nenhum capability profile ativo encontrado para ONLINE na região informada."
            ),
            "region": region,
            "channel": OrderChannel.ONLINE.value,
            "contexts_tried": list(ONLINE_CAPABILITY_CONTEXT_CANDIDATES),
        },
    )


def _normalize_method_candidates(raw_value: str | None) -> set[str]:
    raw = str(raw_value or "").strip()
    lowered = raw.lower()
    uppered = raw.upper()
    compact = lowered.replace("-", "_").replace(" ", "_")
    return {raw, lowered, uppered, compact}


def _normalize_interface_candidates(raw_value: str | None) -> set[str]:
    raw = str(raw_value or "").strip()
    lowered = raw.lower()
    uppered = raw.upper()
    compact = lowered.replace("-", "_").replace(" ", "_")
    return {raw, lowered, uppered, compact}


def _extract_rule_aliases(method_payload: dict) -> set[str]:
    rules = method_payload.get("rules") or {}
    aliases: set[str] = set()

    candidate_keys = (
        "aliases",
        "alias",
        "accepted_inputs",
        "accepted_values",
        "external_codes",
        "legacy_codes",
    )

    for key in candidate_keys:
        value = rules.get(key)
        if isinstance(value, list):
            for item in value:
                aliases.update(_normalize_method_candidates(str(item)))
        elif isinstance(value, str):
            aliases.update(_normalize_method_candidates(value))

    return aliases


def _resolve_method_from_capabilities(
    *,
    capabilities: dict,
    payment_method_value: str,
) -> dict:
    requested_candidates = _normalize_method_candidates(payment_method_value)

    for method_payload in capabilities.get("methods", []):
        method_code = str(method_payload.get("method") or "").strip()
        method_label = str(method_payload.get("label") or "").strip()

        known_candidates = set()
        known_candidates.update(_normalize_method_candidates(method_code))
        if method_label:
            known_candidates.update(_normalize_method_candidates(method_label))
        known_candidates.update(_extract_rule_aliases(method_payload))

        if requested_candidates & known_candidates:
            return method_payload

    raise HTTPException(
        status_code=400,
        detail={
            "type": "UNSUPPORTED_PAYMENT_METHOD",
            "message": f"Método de pagamento não suportado no pedido ONLINE: {payment_method_value}",
            "requested": payment_method_value,
            "allowed": [m.get("method") for m in capabilities.get("methods", [])],
        },
    )


def _resolve_interface_from_method(
    *,
    method_payload: dict,
    payment_interface: str | None,
) -> str | None:
    interfaces = method_payload.get("interfaces") or []
    if not interfaces:
        return None

    if payment_interface:
        requested_candidates = _normalize_interface_candidates(payment_interface)

        for interface_payload in interfaces:
            interface_code = str(interface_payload.get("code") or "").strip()
            interface_label = str(interface_payload.get("label") or "").strip()

            known_candidates = set()
            known_candidates.update(_normalize_interface_candidates(interface_code))
            if interface_label:
                known_candidates.update(_normalize_interface_candidates(interface_label))

            if requested_candidates & known_candidates:
                return interface_code

        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_PAYMENT_INTERFACE",
                "message": f"Interface de pagamento não suportada: {payment_interface}",
                "payment_method": method_payload.get("method"),
                "allowed_interfaces": [item.get("code") for item in interfaces],
            },
        )

    for interface_payload in interfaces:
        if bool(interface_payload.get("default")):
            return str(interface_payload.get("code") or "").strip() or None

    first_code = str(interfaces[0].get("code") or "").strip()
    return first_code or None


def _validate_method_requirements(
    *,
    method_payload: dict,
    amount_cents_input: int | None,
    guest_phone: str | None,
    wallet_provider: str | None,
) -> None:
    requirements = method_payload.get("requirements") or []

    for requirement in requirements:
        if not bool(requirement.get("required")):
            continue

        code = str(requirement.get("code") or "").strip().lower()

        if code in {"customer_phone", "phone", "guest_phone"} and not str(guest_phone or "").strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "MISSING_REQUIRED_FIELD",
                    "message": "customer_phone é obrigatório para o método de pagamento selecionado.",
                    "requirement": code,
                    "payment_method": method_payload.get("method"),
                },
            )

        if code in {"wallet_provider", "wallet"} and not str(wallet_provider or "").strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "MISSING_REQUIRED_FIELD",
                    "message": "wallet_provider é obrigatório para o método de pagamento selecionado.",
                    "requirement": code,
                    "payment_method": method_payload.get("method"),
                },
            )

        if code in {"amount_cents", "amount"} and amount_cents_input is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "MISSING_REQUIRED_FIELD",
                    "message": "amount_cents é obrigatório para o método de pagamento selecionado.",
                    "requirement": code,
                    "payment_method": method_payload.get("method"),
                },
            )

    rules = method_payload.get("rules") or {}

    if bool(rules.get("requires_amount_input")) and amount_cents_input is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MISSING_REQUIRED_FIELD",
                "message": "amount_cents é obrigatório para o método de pagamento selecionado.",
                "payment_method": method_payload.get("method"),
            },
        )

    if bool(rules.get("requires_customer_phone")) and not str(guest_phone or "").strip():
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MISSING_REQUIRED_FIELD",
                "message": "customer_phone é obrigatório para o método de pagamento selecionado.",
                "payment_method": method_payload.get("method"),
            },
        )

    if bool(rules.get("requires_wallet_provider")) and not str(wallet_provider or "").strip():
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MISSING_REQUIRED_FIELD",
                "message": "wallet_provider é obrigatório para o método de pagamento selecionado.",
                "payment_method": method_payload.get("method"),
            },
        )


def _resolve_payment_method_enum_from_db(method_code: str) -> PaymentMethod:
    try:
        return PaymentMethod(method_code)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "UNSUPPORTED_PAYMENT_METHOD_ENUM",
                "message": (
                    "O método retornado pelo capability profile não existe no enum PaymentMethod."
                ),
                "payment_method": method_code,
            },
        ) from exc


# ==================== Função Principal ====================

def create_order_core(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    payment_method_value: str,
    amount_cents_input: int | None,
    guest_phone: str | None,
    user_id: str | None,
    card_type_value: Optional[str] = None,
    payment_interface: Optional[str] = None,
    wallet_provider: Optional[str] = None,
    customer_email: Optional[str] = None,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> CreateOrderCoreResult:
    """
    Criação de pedido ONLINE com source of truth no capability profile do banco.

    Fluxo:
    1. Validar locker_id
    2. Resolver capability profile ONLINE na região
    3. Resolver método/interface/requisitos pelo banco
    4. Validar locker no runtime usando método/interface resolvidos
    5. Validar slot
    6. Resolver pricing
    7. Calcular TTL
    8. Alocar slot no runtime
    9. Persistir order/allocation
    10. Registrar lifecycle
    """
    # =========================
    # 1. VALIDAR LOCKER ID
    # =========================
    totem_id = validate_locker_id_format(totem_id, region)

    # =========================
    # 2. CAPABILITIES (SOURCE OF TRUTH)
    # =========================
    # capabilities = _get_online_capabilities(
    #     db=db,
    #     region=region,
    # )

    # method_payload = _resolve_method_from_capabilities(
    #     capabilities=capabilities,
    #     payment_method_value=payment_method_value,
    # )

    # resolved_method_code = str(method_payload.get("method") or "").strip()
    # if not resolved_method_code:
    #     raise HTTPException(
    #         status_code=400,
    #         detail={
    #             "type": "INVALID_CAPABILITY_METHOD",
    #             "message": "Capability profile retornou método sem code.",
    #             "region": region,
    #             "channel": OrderChannel.ONLINE.value,
    #         },
    #     )

    # resolved_payment_interface = _resolve_interface_from_method(
    #     method_payload=method_payload,
    #     payment_interface=payment_interface,
    # )

    # resolved_wallet_provider = wallet_provider
    # if not resolved_wallet_provider:
    #     wallet_provider_payload = method_payload.get("wallet_provider")
    #     if isinstance(wallet_provider_payload, dict):
    #         resolved_wallet_provider = wallet_provider_payload.get("code")

    # _validate_method_requirements(
    #     method_payload=method_payload,
    #     amount_cents_input=amount_cents_input,
    #     guest_phone=guest_phone,
    #     wallet_provider=resolved_wallet_provider,
    # )

    # payment_method = _resolve_payment_method_enum_from_db(resolved_method_code)


    # novo (banco)
    resolved_payment = resolve_payment_ui_code(
        db=db,
        raw_payment_method=payment_method_value,
        raw_payment_interface=payment_interface,
        raw_wallet_provider=wallet_provider,
    )

    payment_method_value = resolved_payment["payment_method"]
    payment_interface = resolved_payment["payment_interface"]
    wallet_provider = resolved_payment["wallet_provider"]

    # payment_method = payment_method_value # marcos
    payment_method = _resolve_payment_method_enum_from_db(payment_method_value) 




    # =========================
    # 3. VALIDAR LOCKER (SOURCE OF TRUTH)
    # =========================
    validate_locker_for_order(
        db=db,
        locker_id=totem_id,
        region=region,
        channel=OrderChannel.ONLINE.value,
        payment_method=resolved_payment["payment_method"],  # ❌ STRING - marcos isso pode ser um erro aqui
        payment_interface=resolved_payment["payment_interface"],
    )

    # =========================
    # 4. SLOT OBRIGATÓRIO
    # =========================
    if desired_slot is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "DESIRED_SLOT_REQUIRED",
                "message": "desired_slot é obrigatório para pedido ONLINE.",
            },
        )

    try:
        desired_slot = int(desired_slot)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DESIRED_SLOT",
                "message": "desired_slot inválido.",
                "desired_slot": desired_slot,
            },
        ) from exc

    if desired_slot <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DESIRED_SLOT",
                "message": "desired_slot deve ser maior que zero.",
                "desired_slot": desired_slot,
            },
        )

    validate_slot_for_region(desired_slot, region)

    # =========================
    # 5. PRICING (SOURCE OF TRUTH)
    # =========================
    if amount_cents_input is not None:
        if int(amount_cents_input) <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "INVALID_AMOUNT_CENTS",
                    "message": "amount_cents must be > 0",
                },
            )
        amount_cents = int(amount_cents_input)
    else:
        try:
            pricing = backend_client.get_sku_pricing(
                region,
                sku_id,
                locker_id=totem_id,
            )
        except HTTPError as exc:
            if (
                exc.response is not None
                and exc.response.status_code == 404
                and settings.dev_allow_unknown_sku
            ):
                pricing = {"amount_cents": settings.dev_default_price_cents}
            else:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "type": "PRICING_LOOKUP_FAILED",
                        "message": "Falha ao consultar pricing do SKU.",
                        "sku_id": sku_id,
                        "locker_id": totem_id,
                        "region": region,
                    },
                ) from exc

        amount_cents = _extract_pricing_amount_cents(pricing)

    validate_amount_for_region(amount_cents, region)

    # =========================
    # 6. TTL
    # =========================
    alloc_ttl_sec = resolve_online_prepayment_ttl_sec(
        db=db,
        region=region,
        payment_method=payment_method.value,
        amount_cents=amount_cents,
    )

    # =========================
    # 7. ALLOCATION NO RUNTIME
    # =========================
    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            region=region,
            sku_id=sku_id,
            ttl_sec=alloc_ttl_sec,
            request_id=request_id,
            desired_slot=desired_slot,
            locker_id=totem_id,
        )
    except HTTPError as exc:
        runtime_detail = None
        status_code = 502

        if exc.response is not None:
            status_code = 409 if exc.response.status_code == 409 else 502
            try:
                runtime_detail = exc.response.json()
            except Exception:
                runtime_detail = exc.response.text

        raise HTTPException(
            status_code=status_code,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao executar reserva do slot no runtime.",
                "locker_id": totem_id,
                "region": region,
                "desired_slot": desired_slot,
                "request_id": request_id,
                "runtime_detail": runtime_detail,
            },
        ) from exc

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    runtime_state = alloc.get("state")

    if not allocation_id or slot is None:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "INVALID_ALLOCATION_RESPONSE",
                "message": "Resposta inválida do runtime para allocation.",
                "runtime_response": alloc,
            },
        )

    try:
        slot = int(slot)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "INVALID_ALLOCATION_RESPONSE",
                "message": "slot retornado pelo runtime é inválido.",
                "runtime_response": alloc,
            },
        ) from exc

    if slot != desired_slot:
        try:
            backend_client.locker_release(
                region,
                allocation_id,
                locker_id=totem_id,
            )
        except Exception:
            logger.exception(
                "allocation_slot_mismatch_release_failed - allocation_id=%s",
                allocation_id,
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "ALLOCATION_SLOT_MISMATCH",
                "message": "Runtime retornou slot diferente do slot decidido pelo backend central.",
                "desired_slot": desired_slot,
                "runtime_slot": slot,
                "locker_id": totem_id,
                "allocation_id": allocation_id,
                "runtime_state": runtime_state,
            },
        )

    # =========================
    # 8. ORDER
    # =========================
    order = Order(
        id=str(uuid.uuid4()),
        user_id=user_id,
        channel=OrderChannel.ONLINE,
        region=region,
        totem_id=totem_id,
        sku_id=sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        payment_method=payment_method, # enum ✅
        guest_phone=guest_phone,
        customer_email=customer_email,
        device_id=device_id,
        ip_address=ip_address,
        # payment_method=resolved_payment["payment_method"], # ❌ STRING
        payment_interface=resolved_payment["payment_interface"],
    )

    if card_type_value is not None and hasattr(order, "card_type"):
        setattr(order, "card_type", card_type_value)

    payment_timeout_at = datetime.utcnow() + timedelta(seconds=alloc_ttl_sec)

    try:
        db.add(order)
        db.flush()

        allocation = Allocation(
            id=allocation_id,
            order_id=order.id,
            locker_id=totem_id,
            slot=slot,
            state=AllocationState.RESERVED_PENDING_PAYMENT,
            ttl_seconds=alloc_ttl_sec,
            expires_at=payment_timeout_at,
        )

        db.add(allocation)
        db.commit()
        db.refresh(order)
        db.refresh(allocation)
    except Exception as exc:
        db.rollback()

        try:
            backend_client.locker_release(
                region,
                allocation_id,
                locker_id=totem_id,
            )
        except Exception:
            logger.exception(
                "online_order_db_failure_release_failed - allocation_id=%s",
                allocation_id,
            )

        raise HTTPException(
            status_code=500,
            detail={
                "type": "ORDER_PERSISTENCE_FAILED",
                "message": "Falha ao persistir pedido/alocação após reserva no runtime.",
                "order_id": order.id,
                "allocation_id": allocation_id,
                "locker_id": totem_id,
                "slot": slot,
            },
        ) from exc

    # =========================
    # 9. LIFECYCLE
    # =========================
    try:
        register_prepayment_timeout_deadline(
            order_id=order.id,
            order_channel=order.channel.value,
            region_code=order.region,
            slot_id=str(allocation.slot),
            machine_id=order.totem_id,
            created_at=order.created_at,
            payment_method=order.payment_method.value,
            timeout_seconds=alloc_ttl_sec,
        )
    except LifecycleClientError as exc:
        logger.exception(
            "lifecycle_register_failed - order_id=%s, allocation_id=%s",
            order.id,
            allocation.id,
        )
        compensate_failed_online_creation(
            db=db,
            order=order,
            allocation=allocation,
        )
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_REGISTER_FAILED",
                "message": "Falha ao registrar deadline no lifecycle.",
                "order_id": order.id,
                "allocation_id": allocation.id,
                "locker_id": order.totem_id,
                "error": str(exc),
            },
        ) from exc

    logger.info(
        "Order created successfully - order_id=%s, allocation_id=%s, region=%s, "
        "payment_method=%s, amount=%s, ttl_sec=%s, payment_interface=%s, wallet_provider=%s",
        order.id,
        allocation.id,
        region,
        payment_method.value,
        amount_cents,
        alloc_ttl_sec,
        resolved_payment["payment_interface"],
        resolved_payment["wallet_provider"],
    )

    return CreateOrderCoreResult(
        order=order,
        allocation=allocation,
        ttl_sec=alloc_ttl_sec,
        payment_timeout_at=payment_timeout_at,
    )


# ==================== Funções Auxiliares para Métodos Específicos ====================

def create_order_with_pix(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    amount_cents: int,
    guest_phone: str,
    user_id: Optional[str] = None,
) -> CreateOrderCoreResult:
    """Helper para criação de pedido com PIX"""
    return create_order_core(
        db=db,
        region=region,
        sku_id=sku_id,
        totem_id=totem_id,
        desired_slot=desired_slot,
        payment_method_value="pix",
        amount_cents_input=amount_cents,
        guest_phone=guest_phone,
        user_id=user_id,
        payment_interface="qr_code",
    )


def create_order_with_mbway(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    amount_cents: int,
    guest_phone: str,
    user_id: Optional[str] = None,
) -> CreateOrderCoreResult:
    """Helper para criação de pedido com MBWAY"""
    if region != "PT":
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MBWAY_REGION_ERROR",
                "message": "MBWAY só está disponível em Portugal",
            },
        )

    return create_order_core(
        db=db,
        region=region,
        sku_id=sku_id,
        totem_id=totem_id,
        desired_slot=desired_slot,
        payment_method_value="mbway",
        amount_cents_input=amount_cents,
        guest_phone=guest_phone,
        user_id=user_id,
        payment_interface="web_token",
    )


def create_order_with_alipay(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    amount_cents: int,
    user_id: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> CreateOrderCoreResult:
    """Helper para criação de pedido com Alipay (China)"""
    if region != "CN":
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ALIPAY_REGION_ERROR",
                "message": "Alipay só está disponível na China",
            },
        )

    return create_order_core(
        db=db,
        region=region,
        sku_id=sku_id,
        totem_id=totem_id,
        desired_slot=desired_slot,
        payment_method_value="alipay",
        amount_cents_input=amount_cents,
        guest_phone=None,
        user_id=user_id,
        payment_interface="qr_code",
        customer_email=customer_email,
    )


def create_order_with_mpesa(
    *,
    db: Session,
    region: str,
    sku_id: str,
    totem_id: str,
    desired_slot: int,
    amount_cents: int,
    guest_phone: str,
    user_id: Optional[str] = None,
) -> CreateOrderCoreResult:
    """Helper para criação de pedido com M-PESA (África)"""
    allowed_regions = {"KE", "TZ", "UG", "RW"}
    if region not in allowed_regions:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "MPESA_REGION_ERROR",
                "message": f"M-PESA só está disponível em: {', '.join(allowed_regions)}",
            },
        )

    return create_order_core(
        db=db,
        region=region,
        sku_id=sku_id,
        totem_id=totem_id,
        desired_slot=desired_slot,
        payment_method_value="m_pesa",
        amount_cents_input=amount_cents,
        guest_phone=guest_phone,
        user_id=user_id,
        payment_interface="ussd",
    )


