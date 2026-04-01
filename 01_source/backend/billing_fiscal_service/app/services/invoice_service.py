# 01_source/backend/billing_fiscal_service/app/services/invoice_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.integrations.order_pickup_client import OrderPickupClientError, get_order_snapshot
from app.models.invoice_model import Invoice, InvoiceStatus
from app.utils.id_generator import generate_invoice_id


def _country_from_region(region: str | None) -> str:
    normalized = str(region or "").strip().upper()
    mapping = {

        # Brasil e estados
        "SP": "BR",
        "RJ": "BR",
        "MG": "BR",
        "SC": "BR",
        "PR": "BR",
        "RS": "BR",
        "RN": "BR",
        "BA": "BR",
        "PE": "BR",
        "AM": "BR",
        "BR": "BR",
        
        # Portugal
        "PT": "PT",
        
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
    return mapping.get(normalized, "BR")


def _currency_from_country(country: str) -> str:
    mapping = {

        # América Latina
        "BR": "BRL",  # Real Brasileiro
        "AR": "ARS",  # Peso Argentino
        "CL": "CLP",  # Peso Chileno
        "CO": "COP",  # Peso Colombiano
        "MX": "MXN",  # Peso Mexicano
        "UY": "UYU",  # Peso Uruguaio
        "PY": "PYG",  # Guarani Paraguaio
        "PE": "PEN",  # Sol Peruano
        
        # Europa (Euro)
        "PT": "EUR",  # Euro - Portugal
        "ES": "EUR",  # Euro - Espanha
        "FR": "EUR",  # Euro - França
        "IT": "EUR",  # Euro - Itália
        "DE": "EUR",  # Euro - Alemanha
        "NL": "EUR",  # Euro - Holanda
        "BE": "EUR",  # Euro - Bélgica
        "IE": "EUR",  # Euro - Irlanda
        
        # Outros países europeus
        "GB": "GBP",  # Libra Esterlina - Reino Unido
        
        # América do Norte
        "US": "USD",  # Dólar Americano
        "CA": "CAD",  # Dólar Canadense
        
        # África
        "AO": "AOA",  # Kwanza Angolano
        "MZ": "MZN",  # Metical Moçambicano
        "CV": "CVE",  # Escudo Cabo-Verdiano

        # Ásia
        "JP": "YEN",

    }
    return mapping.get(country, "BRL")


def _invoice_type_from_country(country: str) -> str:
    mapping = {

        # América Latina
        "BR": "NFE",        # Nota Fiscal Eletrônica - Brasil
        "AR": "FCE",        # Factura de Crédito Electrónica - Argentina
        "CL": "DTE",        # Documento Tributario Electrónico - Chile
        "CO": "FEL",        # Factura Electrónica - Colômbia
        "MX": "CFDI",       # Comprobante Fiscal Digital por Internet - México
        "UY": "FCE",        # Factura Electrónica - Uruguai
        "PY": "FEL",        # Factura Electrónica - Paraguai
        "PE": "FEL",        # Factura Electrónica - Peru
        
        # Europa (modelos de faturação)
        "PT": "SAFT",       # SAF-T (Standard Audit File for Tax) - Portugal
        "ES": "FACTURAE",   # FacturaE - Espanha
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
    return mapping.get(country, "NFE")


def _extract_order_snapshot_fields(snapshot: dict) -> dict:
    order = snapshot.get("order") or {}
    allocation = snapshot.get("allocation") or {}
    pickup = snapshot.get("pickup") or {}

    region = order.get("region")
    country = _country_from_region(region)

    return {
        "tenant_id": None,
        "region": region,
        "country": country,
        "currency": _currency_from_country(country),
        "payment_method": order.get("payment_method"),
        "amount_cents": order.get("amount_cents"),
        "invoice_type": _invoice_type_from_country(country),
        "order_snapshot": {
            "order": order,
            "allocation": allocation,
            "pickup": pickup,
        },
        "payload_json": {
            "source": "manual_generate_endpoint",
            "trigger_event": "order.paid",
            "lookup_source": "order_pickup_service",
        },
    }


def generate_invoice(db: Session, order_id: str) -> Invoice:
    normalized_order_id = str(order_id).strip()

    existing = db.execute(
        select(Invoice).where(Invoice.order_id == normalized_order_id)
    ).scalar_one_or_none()

    if existing:
        return existing

    if not has_order_paid_event(db, normalized_order_id):
        raise ValueError(
            f"Evento financeiro oficial não encontrado para order_id={normalized_order_id}. "
            f"Esperado: order.paid em domain_events."
        )

    try:
        snapshot = get_order_snapshot(normalized_order_id)
    except OrderPickupClientError as exc:
        raise ValueError(f"Não foi possível enriquecer invoice com dados canônicos do pedido: {exc}") from exc

    fields = _extract_order_snapshot_fields(snapshot)
    now = datetime.now(timezone.utc)

    invoice = Invoice(
        id=generate_invoice_id(),
        order_id=normalized_order_id,
        tenant_id=fields["tenant_id"],
        region=fields["region"],
        country=fields["country"],
        invoice_type=fields["invoice_type"],
        invoice_number=None,
        invoice_series=None,
        access_key=None,
        payment_method=fields["payment_method"],
        currency=fields["currency"],
        amount_cents=fields["amount_cents"],
        status=InvoiceStatus.PENDING,
        xml_content=None,
        payload_json=fields["payload_json"],
        tax_details=None,
        government_response=None,
        order_snapshot=fields["order_snapshot"],
        error_message=None,
        last_error_code=None,
        retry_count=0,
        next_retry_at=None,
        last_attempt_at=None,
        dead_lettered_at=None,
        processing_started_at=None,
        locked_by=None,
        locked_at=None,
        issued_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice