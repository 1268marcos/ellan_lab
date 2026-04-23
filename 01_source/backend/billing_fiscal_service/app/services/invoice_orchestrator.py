# 01_source/backend/biling_fiscal_service/app/services/invoice_orchestrator.py
# Arquivo preserva o endpoint manual como fallback, mas agora ele usa o mesmo mecanismo de lock/processamento dos workers.
# 11/04/2026 - aplicação de patch de: raise Valuerror(str(exc)) para: raise OrderPickupClientError(str(exc))

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.integrations.order_pickup_client import (
    OrderPickupClientError,
    get_order_snapshot_for_invoice,
)
from app.models.invoice_model import Invoice
from app.services.invoice_processing_service import claim_and_process_invoice_by_id
from app.services.invoice_snapshot_fiscal import fiscal_columns_from_order_snapshot

logger = logging.getLogger(__name__)


# 🔥 CORREÇÃO 3 — REGION GENÉRICA (NÃO APENAS SP/PT)
def _normalize_region(region: str | None) -> str | None:
    if region is None:
        return None
    return str(region).strip().upper()


def _resolve_country_from_snapshot(snapshot: dict) -> str:
    order = snapshot.get("order") or {}
    region_raw = order.get("region")
    
    # 🔥 CORREÇÃO: Normaliza e valida a região
    region = _normalize_region(region_raw)
    
    if not region:
        raise ValueError(
            f"Campo 'region' é obrigatório no snapshot do pedido. "
            f"Valor recebido: {region_raw!r}. order_id: {snapshot.get('order', {}).get('id')}"
        )
    
    # 🔥 CORREÇÃO: Mapeamento genérico baseado em regras de negócio
    # Mapeia regiões para países conforme necessidade fiscal
    region_to_country = {
        "AC": "BR", "AL": "BR", "AP": "BR", "AM": "BR", "BA": "BR",
        "CE": "BR", "DF": "BR", "ES": "BR", "GO": "BR", "MA": "BR",
        "MG": "BR", "MS": "BR", "MT": "BR", "PA": "BR", "PB": "BR",
        "PE": "BR", "PI": "BR", "PR": "BR", "RJ": "BR", "RN": "BR",
        "RO": "BR", "RR": "BR", "RS": "BR", "SC": "BR", "SE": "BR",
        "SP": "BR", "TO": "BR", 

        "PT": "PT",
        "BR": "BR",  # Caso a região já venha como BR

        # Espanha
        "ES": "ES",
        
        # América Latina
        "AR": "AR",  # Argentina
        "CL": "CL",  # Chile
        "CO": "CO",  # Colômbia
        "MX": "MX",  # México
        "UY": "UY",  # Uruguai
        "PY": "PY",  # Paraguai
        "PE": "PE",  # Peru

        # Europa
        "FR": "FR",  # França
        "IT": "IT",  # Itália
        "DE": "DE",  # Alemanha
        "NL": "NL",  # Holanda
        "BE": "BE",  # Bélgica
        "GB": "GB",  # Reino Unido
        "IE": "IE",  # Irlanda
        
        # América do Norte
        "US": "US",  # Estados Unidos
        "CA": "CA",  # Canadá
        
        # África
        "AO": "AO",  # Angola
        "MZ": "MZ",  # Moçambique
        "CV": "CV",  # Cabo Verde

        # Ásia
        "JP": "JP",

    }
    
    # Se a região for um código de país direto (ex: "BR", "PT", "US")
    if region in ["BR", "PT", "ES", "AR", "MX", "CO", "CL", "PE", "UY", "PY", "FR", "IT", "DE", "NL", "BE", "GB", "IE", "US", "CA", "AO", "MZ", "CV", "JP"]:
        return region
    
    # Tenta mapear a região para um país
    country = region_to_country.get(region)
    
    if country is None:
        # Log de warning para regiões não mapeadas
        logger.warning(
            "unknown_region_mapping",
            extra={
                "region": region,
                "original_region": region_raw,
                "defaulting_to_BR": "BR",
                "order_id": snapshot.get("order", {}).get("id"),
            },
        )
        # 🔥 CORREÇÃO: Fallback genérico para BR (ou configurável)
        return "BR"
    
    return country


def _resolve_invoice_type(country: str) -> str:
    normalized = str(country or "").strip().upper()

    # 🔥 CORREÇÃO: Mapeamento genérico por país
    country_invoice_map = {
        "BR": "NFE",
        "PT": "SAFT",
        "ES": "FACTURAE",
        # América Latina
        "AR": "FCE",
        "MX": "CFDI",
        "CO": "FEL",
        "CL": "DTE",
        "PE": "FEL",
        "UY": "FCE",
        "PY": "FEL",
        # Europa (modelos de faturação)
        "FR": "FACTURE",    # Facture électronique - França
        "IT": "FATTURA",    # Fattura Elettronica - Itália
        "DE": "XREchnung",  # XRechnung - Alemanha
        "NL": "UBL",        # UBL Invoice - Holanda
        "BE": "UBL",        # UBL Invoice - Bélgica
        "IE": "UBL",        # UBL Invoice - Irlanda
        # Outros países
        "GB": "INVOICE",    # E-invoice - Reino Unido
        "US": "INVOICE",    # Invoice - EUA
        "CA": "INVOICE",    # Invoice - Canadá
        "AO": "FATURA",     # Fatura Electrónica - Angola
        "MZ": "FATURA",     # Fatura Electrónica - Moçambique
        "CV": "FATURA",     # Fatura Electrónica - Cabo Verde

    }
    
    invoice_type = country_invoice_map.get(normalized)
    
    if invoice_type is None:
        logger.warning(
            "unknown_invoice_type_for_country",
            extra={
                "country": country,
                "defaulting_to_INVOICE": "INVOICE",
            },
        )
        return "INVOICE"
    
    return invoice_type


def ensure_invoice_for_order(db: Session, order_id: str) -> Invoice:
    normalized_order_id = str(order_id).strip()

    existing = (
        db.query(Invoice)
        .filter(Invoice.order_id == normalized_order_id)
        .first()
    )
    if existing:
        return existing

    if not has_order_paid_event(db, normalized_order_id):
        raise ValueError(
            f"Evento financeiro oficial não encontrado para order_id={normalized_order_id}. "
            f"Esperado: order.paid em domain_events."
        )

    try:
        snapshot = get_order_snapshot_for_invoice(normalized_order_id)
    except OrderPickupClientError as exc:
        # raise ValueError(str(exc)) from exc
        raise OrderPickupClientError(str(exc)) from exc

    order = snapshot.get("order") or {}
    
    # 🔥 CORREÇÃO: Usa a nova função com validação
    try:
        country = _resolve_country_from_snapshot(snapshot)
    except ValueError as exc:
        # Re-raise com contexto mais claro
        raise ValueError(f"Falha ao resolver país para order_id={normalized_order_id}: {exc}") from exc
    
    invoice_type = _resolve_invoice_type(country)

    fiscal_cols = fiscal_columns_from_order_snapshot(snapshot, country=country)

    invoice = Invoice(
        id=f"inv_{uuid.uuid4().hex}",
        order_id=normalized_order_id,
        tenant_id=order.get("tenant_id") or (snapshot.get("tenant_fiscal") or {}).get("tenant_id"),
        region=order.get("region"),
        country=country,
        invoice_type=invoice_type,
        payment_method=order.get("payment_method"),
        currency=order.get("currency") or ("BRL" if country == "BR" else "EUR"),
        amount_cents=order.get("amount_cents"),
        order_snapshot=snapshot,
        **fiscal_cols,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    logger.info(
        "invoice_created_from_order_paid",
        extra={
            "order_id": normalized_order_id,
            "invoice_id": invoice.id,
            "country": country,
            "invoice_type": invoice_type,
        },
    )

    return invoice


def ensure_and_process_invoice(db: Session, order_id: str) -> Invoice:
    invoice = ensure_invoice_for_order(db, order_id)

    processed = claim_and_process_invoice_by_id(
        db,
        invoice_id=invoice.id,
    )

    if processed is None:
        invoice = db.query(Invoice).filter(Invoice.id == invoice.id).first()
        return invoice

    return processed