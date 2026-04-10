# 01_source/order_pickup_service/app/services/payment_confirm_service.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# veja o final do arquivo
# 09/04/2026 - Incluído número de tentativas

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Dict, Tuple
from enum import Enum

from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.domain_event_outbox import DomainEventOutbox
from app.models.fiscal_document import FiscalDocument
from app.models.order import Order, PaymentMethod, OrderChannel, PaymentStatus
from app.services.domain_event_outbox_service import enqueue_order_paid_event
from app.services import backend_client

logger = logging.getLogger(__name__)


# ==================== Enums e Constantes ====================

class FiscalDocumentType(str, Enum):
    """Tipos de documento fiscal por região"""
    NFE = "NFE"  # Brasil - Nota Fiscal Eletrônica
    NFC_E = "NFC_E"  # Brasil - NFC-e (Cupom Fiscal Eletrônico)
    SAT = "SAT"  # Brasil - Sistema Autenticador e Transmissor
    FISCAL_RECEIPT_SIMULATED = "FISCAL_RECEIPT_SIMULATED"  # Simulado
    INVOICE = "INVOICE"  # Europa/Ásia - Fatura comercial
    TAX_INVOICE = "TAX_INVOICE"  # Singapura/Austrália
    RECEIPT = "RECEIPT"  # EUA/Canadá - Recibo simples
    ETR = "ETR"  # Emirados Árabes - Electronic Tax Register


class DocumentDeliveryMode(str, Enum):
    """Modo de entrega do documento fiscal"""
    PRINT = "PRINT"  # Impressão local
    SEND = "SEND"    # Envio por email/SMS
    BOTH = "BOTH"    # Ambos
    QR_CODE = "QR_CODE"  # QR Code para download


# Configurações fiscais por região
REGION_FISCAL_CONFIG = {
    # Brasil
    "SP": {"document_type": FiscalDocumentType.NFE, "delivery_mode": DocumentDeliveryMode.BOTH},
    "RJ": {"document_type": FiscalDocumentType.NFE, "delivery_mode": DocumentDeliveryMode.BOTH},
    "MG": {"document_type": FiscalDocumentType.NFE, "delivery_mode": DocumentDeliveryMode.BOTH},
    "RS": {"document_type": FiscalDocumentType.NFE, "delivery_mode": DocumentDeliveryMode.BOTH},
    "BA": {"document_type": FiscalDocumentType.NFE, "delivery_mode": DocumentDeliveryMode.BOTH},
    
    # Portugal
    "PT": {"document_type": FiscalDocumentType.INVOICE, "delivery_mode": DocumentDeliveryMode.SEND},
    
    # México
    "MX": {"document_type": FiscalDocumentType.INVOICE, "delivery_mode": DocumentDeliveryMode.BOTH},
    
    # Argentina
    "AR": {"document_type": FiscalDocumentType.INVOICE, "delivery_mode": DocumentDeliveryMode.PRINT},
    
    # China
    "CN": {"document_type": FiscalDocumentType.INVOICE, "delivery_mode": DocumentDeliveryMode.QR_CODE},
    
    # Japão
    "JP": {"document_type": FiscalDocumentType.INVOICE, "delivery_mode": DocumentDeliveryMode.BOTH},
    
    # Singapura
    "SG": {"document_type": FiscalDocumentType.TAX_INVOICE, "delivery_mode": DocumentDeliveryMode.SEND},
    
    # Austrália
    "AU": {"document_type": FiscalDocumentType.TAX_INVOICE, "delivery_mode": DocumentDeliveryMode.SEND},
    
    # Emirados Árabes
    "AE": {"document_type": FiscalDocumentType.ETR, "delivery_mode": DocumentDeliveryMode.QR_CODE},
    
    # EUA
    "US": {"document_type": FiscalDocumentType.RECEIPT, "delivery_mode": DocumentDeliveryMode.SEND},
    
    # Padrão
    "DEFAULT": {"document_type": FiscalDocumentType.FISCAL_RECEIPT_SIMULATED, "delivery_mode": DocumentDeliveryMode.PRINT},
}


# ==================== Funções Utilitárias ====================

def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _enum_value_or_raw(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _get_region_base(region: str) -> str:
    region_upper = str(region or "").strip().upper()

    if region_upper in {"AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
        "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
        "RO", "RR", "RS", "SC", "SE", "SP", "TO"}:
        return "BR"

    if region_upper.startswith("US_"):
        return "US"
    if region_upper.startswith("CA_"):
        return "CA"
    if len(region_upper) >= 2:
        return region_upper[:2]
    return region_upper


def _get_fiscal_config(region: str) -> Dict[str, Any]:
    """Retorna configuração fiscal para a região"""
    region_base = _get_region_base(region)
    config = REGION_FISCAL_CONFIG.get(region_base, REGION_FISCAL_CONFIG["DEFAULT"])
    return config


def _ensure_unique_receipt_code(
    db: Session,
    receipt_code: str,
    max_attempts: int = 3,
) -> str:
    """Garante que o receipt_code é único no banco"""
    existing = db.query(FiscalDocument).filter(
        FiscalDocument.receipt_code == receipt_code
    ).first()
    
    if not existing:
        return receipt_code
    
    # Se colidiu, tenta com hash diferente
    for i in range(1, max_attempts + 1):
        # Modifica o digest com um seed
        parts = receipt_code.split('-')
        if len(parts) >= 3:
            # Adiciona sufixo de tentativa
            new_code = f"{parts[0]}-{parts[1]}-{parts[2][:6]}{i:02d}"
            if len(parts) == 4:
                new_code = f"{new_code}-{parts[3]}"
            
            existing = db.query(FiscalDocument).filter(
                FiscalDocument.receipt_code == new_code
            ).first()
            
            if not existing:
                return new_code
    
    # Fallback: adiciona UUID curto
    return f"{receipt_code}-{uuid.uuid4().hex[:4].upper()}"


def _build_fiscal_receipt_code(
    *, 
    order: Order, 
    region: str,
    sequence: Optional[int] = None,
    attempt: int = 1,
) -> str:
    """Gera código de recibo fiscal baseado na região com validação de unicidade"""
    channel = _enum_value_or_raw(order.channel) or "UNK"
    region_base = _get_region_base(region)
    
    # Prefixos por região com fallback
    prefix_map = {
        "BR": "BR", "PT": "PT", "MX": "MX", 
        "AR": "AR", "CN": "CN", "JP": "JP",
        "SG": "SG", "AE": "AE", "AU": "AU", "US": "US"
    }
    
    prefix = prefix_map.get(region_base, "ZZ")  # ZZ = Default
    
    # Canal: KIOSK (KSK) ou ONLINE (ONL)
    channel_prefix = "KSK" if channel == "KIOSK" else "ONL"
    
    # Hash com timestamp para maior unicidade
    timestamp = int(datetime.now().timestamp())
    hash_input = f"{prefix}:{channel}:{order.id}:{attempt}:{timestamp}"
    digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8].upper()
    
    # Adiciona tentativa no código para rastreabilidade
    if attempt > 1:
        return f"{prefix}-{channel_prefix}-{digest}-ATT{attempt:02d}"
    
    if sequence:
        return f"{prefix}-{channel_prefix}-{digest}-{sequence:04d}"
    
    return f"{prefix}-{channel_prefix}-{digest}"


def _build_fiscal_simulation_payload(
    *,
    order: Order,
    allocation: Allocation,
    pickup,
    currency: str,
    transaction_id: Optional[str] = None,
    attempt: int = 1,
) -> dict[str, Any]:
    """Constrói payload de simulação fiscal com suporte regional"""
    
    # Obtém configuração fiscal da região
    fiscal_config = _get_fiscal_config(order.region)
    
    receipt_code = _build_fiscal_receipt_code(
        order=order,
        region=order.region,
        attempt=attempt,
    )
    
    # Determina target de envio
    send_target = (
        getattr(order, "receipt_email", None)
        or getattr(order, "guest_email", None)
        or getattr(order, "receipt_phone", None)
        or getattr(order, "guest_phone", None)
    )
    
    channel = _enum_value_or_raw(order.channel)
    region = str(getattr(order, "region", "") or "").strip().upper()
    payment_method = _enum_value_or_raw(getattr(order, "payment_method", None))
    
    document_type = fiscal_config["document_type"].value
    delivery_mode = fiscal_config["delivery_mode"].value
    
    # Ajusta para KIOSK
    if channel == "KIOSK" and delivery_mode == "SEND":
        delivery_mode = "PRINT"
    
    # Ajusta para regiões que exigem QR Code
    if delivery_mode == "QR_CODE":
        qr_code_url = f"/public/fiscal/qr/{receipt_code}"
    else:
        qr_code_url = None
    
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
            if (delivery_mode in ["SEND", "BOTH"] and send_target)
            else "SIMULATED_NOT_REQUESTED"
        ),
        "send_target": send_target,
        "print_status": (
            "SIMULATED_AVAILABLE"
            if delivery_mode in ["PRINT", "BOTH"]
            else "SIMULATED_NOT_APPLICABLE"
        ),
        "print_site_path": f"/public/fiscal/print/{receipt_code}",
        "json_site_path": f"/public/fiscal/by-code/{receipt_code}",
        "qr_code_url": qr_code_url,
        "print_label": "Use este código no site de impressão do comprovante/cupom simulado.",
        "transaction_id": transaction_id,
        "order": {
            "id": order.id,
            "channel": channel,
            "region": order.region,
            "totem_id": getattr(order, "totem_id", None),
            "sku_id": getattr(order, "sku_id", None),
            "amount_cents": getattr(order, "amount_cents", None),
            "payment_method": payment_method,
            "gateway_transaction_id": getattr(order, "gateway_transaction_id", None),
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "pickup_deadline_at": order.pickup_deadline_at.isoformat() if getattr(order, "pickup_deadline_at", None) else None,
        },
        "allocation": {
            "id": allocation.id if allocation else None,
            "locker_id": allocation.locker_id if allocation else None,
            "slot": allocation.slot if allocation else None,
            "state": _enum_value_or_raw(getattr(allocation, "state", None)) if allocation else None,
        },
        "pickup": {
            "id": getattr(pickup, "id", None) if pickup else None,
            "locker_id": getattr(pickup, "locker_id", None) if pickup else None,
            "machine_id": getattr(pickup, "machine_id", None) if pickup else None,
            "slot": getattr(pickup, "slot", None) if pickup else None,
            "status": _enum_value_or_raw(getattr(pickup, "status", None)) if pickup else None,
            "lifecycle_stage": _enum_value_or_raw(getattr(pickup, "lifecycle_stage", None)) if pickup else None,
        },
    }


def _validate_payment_confirmation(
    order: Order,
    amount_cents: int | None,
    currency: str | None,
) -> None:
    """Valida dados da confirmação de pagamento"""
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
    
    # Verifica se pedido já foi pago
    if order.payment_status == PaymentStatus.APPROVED:
        logger.warning(f"Order already paid: {order.id}")
        raise ValueError(f"Pedido {order.id} já foi pago anteriormente")


# ==================== Funções Principais ====================

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
    Aplica confirmação de pagamento ao pedido.
    Suporta múltiplos métodos de pagamento e regiões.
    """
    # Validação
    _validate_payment_confirmation(order, amount_cents, currency)
    
    # Atualiza método de pagamento se fornecido
    if payment_method:
        order.payment_method = payment_method

    # Atualiza transaction_id
    if transaction_id and str(transaction_id).strip():
        order.gateway_transaction_id = str(transaction_id).strip()

    if not order.gateway_transaction_id:
        order.gateway_transaction_id = f"{source}-{order.id}"

    # Atualiza timestamps
    if not getattr(order, "paid_at", None):
        order.paid_at = _utc_now_naive()
    
    # Atualiza moeda
    if currency:
        order.currency = str(currency).strip().upper()

    # Marca pagamento como aprovado
    order.mark_payment_approved(transaction_id=order.gateway_transaction_id)

    # Marca pedido como pago
    order.mark_as_paid()

    db.commit()

    logger.info(
        "payment_confirmation_applied",
        extra={
            "order_id": order.id,
            "source": source,
            "payment_method": _enum_value_or_raw(order.payment_method),
            "transaction_id": order.gateway_transaction_id,
            "amount_cents": order.amount_cents,
            "currency": str(currency).strip().upper(),
            "region": order.region,
        },
    )


def emit_order_paid_and_simulate_fiscal(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup,
    amount_cents,
    currency: str,
    source: str,
    transaction_id: Optional[str] = None,
    skip_locker_commit,
    attempt: int = 1,
) -> dict[str, Any]:
    """
    Emite evento de pagamento e simula documento fiscal.
    Suporta diferentes formatos fiscais por região.
    """
    if order is None:
        raise ValueError("order obrigatório")

    if allocation is None:
        raise ValueError("allocation obrigatório")

    if not currency or not str(currency).strip():
        raise ValueError("currency obrigatória")

    # Gera event key única
    event_key = f"order.paid:{order.id}:{order.paid_at.isoformat() if order.paid_at else 'now'}"

    # Verifica se evento já existe
    existing = (
        db.query(DomainEventOutbox)
        .filter(DomainEventOutbox.event_key == event_key)
        .first()
    )

    event_already_exists = existing is not None

    # Enfileira evento se necessário
    if not existing:
        enqueue_order_paid_event(
            db,
            order_id=order.id,
            region=order.region,
            channel=_enum_value_or_raw(order.channel),
            payment_method=_enum_value_or_raw(order.payment_method),
            transaction_id=order.gateway_transaction_id or transaction_id,
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
                "region": order.region,
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

    # Normaliza moeda
    currency_norm = str(currency).strip().upper()
    
    # Obtém configuração fiscal da região
    fiscal_config = _get_fiscal_config(order.region)

    # Verifica se documento fiscal já existe
    existing_fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )

    if existing_fiscal:
        # Se já existe e é uma reimpressão (attempt > 1), permite regenerar
        if attempt > 1:
            logger.info(
                "fiscal_document_regeneration_requested",
                extra={
                    "order_id": order.id,
                    "old_receipt_code": existing_fiscal.receipt_code,
                    "new_attempt": attempt,
                },
            )
            # Remove documento existente para gerar novo
            db.delete(existing_fiscal)
            db.flush()
            existing_fiscal = None
        else:
            fiscal = existing_fiscal.payload_json
            logger.info(
                "fiscal_document_already_exists",
                extra={
                    "order_id": order.id,
                    "receipt_code": existing_fiscal.receipt_code,
                },
            )
    
    if not existing_fiscal:
        # Constrói payload fiscal com attempt
        fiscal = _build_fiscal_simulation_payload(
            order=order,
            allocation=allocation,
            pickup=pickup,
            currency=currency_norm,
            transaction_id=transaction_id,
            attempt=attempt,
        )
        
        # Garante unicidade do receipt_code
        unique_receipt_code = _ensure_unique_receipt_code(db, fiscal["receipt_code"])
        if unique_receipt_code != fiscal["receipt_code"]:
            logger.warning(
                "receipt_code_collision_resolved",
                extra={
                    "original_code": fiscal["receipt_code"],
                    "resolved_code": unique_receipt_code,
                    "order_id": order.id,
                },
            )
            fiscal["receipt_code"] = unique_receipt_code
            fiscal["print_site_path"] = f"/public/fiscal/print/{unique_receipt_code}"
            fiscal["json_site_path"] = f"/public/fiscal/by-code/{unique_receipt_code}"
            if fiscal.get("qr_code_url"):
                fiscal["qr_code_url"] = f"/public/fiscal/qr/{unique_receipt_code}"

        # Cria documento fiscal
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
                "region": order.region,
                "document_type": fiscal["document_type"],
                "attempt": attempt,
            },
        )

    # Commit final
    db.commit()

    logger.info(
        "payment_confirm_fiscal_simulated",
        extra={
            "order_id": order.id,
            "receipt_code": fiscal["receipt_code"],
            "delivery_mode": fiscal["delivery_mode"],
            "source": source,
            "region": order.region,
            "attempt": attempt,
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
    transaction_id: Optional[str] = None,
    skip_locker_commit: bool = False,
    attempt: int = 1,
) -> dict[str, Any]:
    """
    Confirma pagamento, commita no runtime e emite eventos.
    Função principal para fluxo de confirmação de pagamento.
    
    Args:
        skip_locker_commit: Para testes ou quando o commit já foi feito
        attempt: Número da tentativa de emissão (1 = primeira, 2+ = reimpressão)
    """
    # =========================
    # 1. Valida + aplica pagamento
    # =========================
    apply_payment_confirmation(
        db=db,
        order=order,
        transaction_id=transaction_id or getattr(order, "gateway_transaction_id", None),
        payment_method=getattr(order, "payment_method", None),
        amount_cents=amount_cents,
        currency=currency,
        source=source,
    )

    # =========================
    # 2. Commit no runtime (se necessário)
    # =========================

    if not skip_locker_commit:
        # 🔒 sanity check (produção)
        if not allocation.locker_id:
            raise ValueError(
                f"locker_id ausente na allocation {allocation.id}"
            )

        try:
            backend_client.locker_commit(
                region=order.region,
                locker_id=allocation.locker_id,  # 🔥 ESSENCIAL
                allocation_id=allocation.id,
            )
            logger.info(
                "locker_commit_success",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "locker_id": allocation.locker_id, 
                    "region": order.region,
                },
            )
        except Exception as e:
            logger.error(
                "locker_commit_failed",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "locker_id": allocation.locker_id, 
                    "region": order.region,
                    "error": str(e),
                },
            )
            raise

    # =========================
    # 3. Atualiza estado local
    # =========================
    allocation.mark_reserved_paid_pending_pickup()

    # =========================
    # 4. Emite evento + fiscal
    # =========================
    return emit_order_paid_and_simulate_fiscal(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        currency=str(currency or "").strip().upper(),
        source=source,
        transaction_id=transaction_id,
        attempt=attempt,
    )


# ==================== Funções Adicionais ====================

def refund_payment(
    *,
    db: Session,
    order: Order,
    amount_cents: Optional[int] = None,
    reason: str,
    source: str,
) -> Dict[str, Any]:
    """
    Processa reembolso de pagamento.
    """
    if order.payment_status != PaymentStatus.APPROVED:
        raise ValueError(f"Order {order.id} not in APPROVED state for refund")
    
    refund_amount = amount_cents or order.amount_cents
    
    if refund_amount > order.amount_cents:
        raise ValueError(f"Refund amount {refund_amount} exceeds order amount {order.amount_cents}")
    
    # Marca como reembolsado
    if refund_amount == order.amount_cents:
        order.mark_payment_refunded()
    else:
        order.payment_status = PaymentStatus.PARTIALLY_REFUNDED
        if order.order_metadata is None:
            order.order_metadata = {}
        order.order_metadata["refunded_amount"] = refund_amount
        order.order_metadata["refund_reason"] = reason
        order.order_metadata["refund_source"] = source
    
    db.commit()
    
    logger.info(
        "payment_refunded",
        extra={
            "order_id": order.id,
            "refund_amount": refund_amount,
            "reason": reason,
            "source": source,
        },
    )
    
    return {
        "order_id": order.id,
        "refund_amount": refund_amount,
        "refunded_at": _utc_now_naive().isoformat(),
        "status": order.payment_status.value,
    }


def get_fiscal_document_by_order(
    db: Session,
    order_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Recupera documento fiscal de um pedido.
    """
    fiscal = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order_id)
        .first()
    )
    
    if fiscal:
        return fiscal.payload_json
    
    return None


def regenerate_fiscal_document(
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup,
    currency: str,
) -> Dict[str, Any]:
    """
    Regenera documento fiscal (útil para reimpressão).
    Incrementa o número de tentativas automaticamente.
    """
    # Busca documento existente para saber quantas tentativas já houve
    existing = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order.id)
        .first()
    )
    
    # Calcula próximo número de tentativa
    next_attempt = 1
    if existing:
        # Tenta extrair attempt do receipt_code existente
        # Padrões: ATT02, ATT03, etc.
        match = re.search(r'-ATT(\d{2})', existing.receipt_code)
        if match:
            last_attempt = int(match.group(1))
            next_attempt = last_attempt + 1
        else:
            # Se não tem ATT, é a primeira tentativa
            next_attempt = 2
    
    # Gera novo documento com attempt incrementado
    result = emit_order_paid_and_simulate_fiscal(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        currency=currency,
        source=f"regenerate_attempt_{next_attempt}",
        attempt=next_attempt,
    )
    
    logger.info(
        f"Fiscal document regenerated for order {order.id}",
        extra={
            "order_id": order.id,
            "attempt": next_attempt,
            "previous_receipt_code": existing.receipt_code if existing else None,
        }
    )
    
    return result



"""

1. Suporte Fiscal por Região:
FiscalDocumentType: Tipos de documento por região (NFE, NFC-e, SAT, INVOICE, TAX_INVOICE, ETR, RECEIPT)

DocumentDeliveryMode: Modos de entrega (PRINT, SEND, BOTH, QR_CODE)

REGION_FISCAL_CONFIG: Configurações específicas para cada mercado

2. Código de Recibo Regional:
Prefixos específicos por região (BR, PT, MX, CN, JP, SG, AE, AU, US)

Hash baseado na região para unicidade

Suporte a sequência numérica

3. Validações Aprimoradas:
_validate_payment_confirmation(): Validação centralizada

Verificação de pagamento duplicado

Validação de moeda e valores

4. QR Code para Documentos Fiscais:
Suporte a QR Code para China e Emirados Árabes

URL de QR Code na resposta

5. Funções Adicionais:
refund_payment(): Processamento de reembolso (total/parcial)

get_fiscal_document_by_order(): Consulta de documento fiscal

regenerate_fiscal_document(): Regeneração de documento

6. Suporte a Reembolso Parcial:
Reembolso total ou parcial

Metadados para controle

Status PARTIALLY_REFUNDED

7. Logging Aprimorado:
Logs com contexto regional

Informações de documento fiscal

Tracking de eventos

8. Parâmetro skip_locker_commit:
Útil para testes

Quando o commit já foi realizado externamente

9. Event Key Única:
Inclui timestamp para unicidade

Previne duplicação de eventos

10. Compatibilidade:
Mantém funções existentes

Adiciona novos parâmetros opcionais

Sem breaking changes

"""