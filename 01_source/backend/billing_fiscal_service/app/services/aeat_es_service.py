# 01_source/backend/billing_fiscal_service/app/services/aeat_es_service.py
# (stub) ESPANHA - Agencia Estatal de Administración Tributaria (AEAT), também conhecida como Agência Tributária
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.invoice_model import Invoice

from app.core.datetime_utils import to_iso_utc


def _aeat_es_now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))


def _aeat_es_generate_invoice_number(invoice: Invoice) -> str:
    return f"ES{datetime.now(timezone.utc).strftime('%Y%m%d')}{str(invoice.id)[-6:].upper()}"


def _aeat_es_generate_series() -> str:
    return "AEATES-1"


def _aeat_es_generate_access_key(invoice: Invoice) -> str:
    return f"aeat_es_{uuid.uuid4().hex}"


def aeat_es_issue_invoice(invoice: Invoice) -> dict:
    invoice_number = _aeat_es_generate_invoice_number(invoice)
    invoice_series = _aeat_es_generate_series()
    access_key = _aeat_es_generate_access_key(invoice)

    return {
        "provider": "aeat_es",
        "country": "ES",
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": {
            "country": "ES",
            "authority": "AEAT",
            "taxes": [
                {
                    "tax_type": "IVA",
                    "tax_rate": 0.0,
                    "tax_amount": 0.0,
                    "note": "Stub inicial AEAT/ES.",
                }
            ],
            "calculated_at": _aeat_es_now_iso(),
        },
        "xml_content": {
            "format": "facturae_stub",
            "authority": "AEAT",
            "invoice_number": invoice_number,
            "invoice_series": invoice_series,
            "access_key": access_key,
            "generated_at": _aeat_es_now_iso(),
        },
        "government_response": {
            "provider_namespace": "aeat_es",
            "provider_status": "ACCEPTED",
            "provider_code": "AEAT-200",
            "provider_message": "Documento fiscal aceite pela AEAT (stub).",
            "processed_at": _aeat_es_now_iso(),
        },
    }


def aeat_es_cc_e_stub(invoice: Invoice, correction_text: str | None) -> dict:
    text = (correction_text or "").strip() or "Corrección documental (stub)."
    return {
        "provider": "aeat_es",
        "kind": "correction_stub",
        "country": "ES",
        "access_key": invoice.access_key or _aeat_es_generate_access_key(invoice),
        "correction_text": text[:1000],
        "processed_at": _aeat_es_now_iso(),
    }


def aeat_es_cancel_invoice(invoice: Invoice) -> dict:
    """Stub I-2 — anulação ES (AEAT real em F-3)."""
    return {
        "provider": "aeat_es",
        "country": "ES",
        "cancel_status": "STUB_CANCELLED",
        "access_key": invoice.access_key or _aeat_es_generate_access_key(invoice),
        "processed_at": _aeat_es_now_iso(),
    }
