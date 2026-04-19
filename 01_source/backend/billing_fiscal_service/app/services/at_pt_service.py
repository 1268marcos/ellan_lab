# 01_source/backend/billing_fiscal_service/app/services/at_pt_service.py
# (stub) PT - Autoridade Tributária
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.invoice_model import Invoice

from app.core.datetime_utils import to_iso_utc



def _at_pt_now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))


def _at_pt_generate_invoice_number(invoice: Invoice) -> str:
    return f"PT{datetime.now(timezone.utc).strftime('%Y%m%d')}{str(invoice.id)[-6:].upper()}"


def _at_pt_generate_series() -> str:
    return "ATPT-1"


def _at_pt_generate_access_key(invoice: Invoice) -> str:
    return f"at_pt_{uuid.uuid4().hex}"


def at_pt_issue_invoice(invoice: Invoice) -> dict:
    invoice_number = _at_pt_generate_invoice_number(invoice)
    invoice_series = _at_pt_generate_series()
    access_key = _at_pt_generate_access_key(invoice)

    return {
        "provider": "at_pt",
        "country": "PT",
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": {
            "country": "PT",
            "authority": "AT",
            "taxes": [
                {
                    "tax_type": "IVA",
                    "tax_rate": 0.0,
                    "tax_amount": 0.0,
                    "note": "Stub inicial AT/PT.",
                }
            ],
            "calculated_at": _at_pt_now_iso(),
        },
        "xml_content": {
            "format": "saft_stub",
            "authority": "AT",
            "invoice_number": invoice_number,
            "invoice_series": invoice_series,
            "access_key": access_key,
            "generated_at": _at_pt_now_iso(),
        },
        "government_response": {
            "provider_namespace": "at_pt",
            "provider_status": "ACCEPTED",
            "provider_code": "AT-200",
            "provider_message": "Documento fiscal aceite pela AT (stub).",
            "processed_at": _at_pt_now_iso(),
        },
    }
