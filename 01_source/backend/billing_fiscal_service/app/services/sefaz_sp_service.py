# 01_source/backend/billing_fiscal_service/app/services/sefaz_sp_service.py
# (stub)
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.invoice_model import Invoice


def _sefaz_sp_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sefaz_sp_generate_invoice_number(invoice: Invoice) -> str:
    return f"SP{datetime.now(timezone.utc).strftime('%Y%m%d')}{str(invoice.id)[-6:].upper()}"


def _sefaz_sp_generate_series() -> str:
    return "SP-1"


def _sefaz_sp_generate_access_key(invoice: Invoice) -> str:
    return f"sefaz_sp_{uuid.uuid4().hex}"


def _sefaz_sp_build_tax_details(invoice: Invoice) -> dict:
    return {
        "country": "BR",
        "authority": "SEFAZ-SP",
        "regime": "stub_simples_nacional",
        "taxes": [
            {
                "tax_type": "ICMS",
                "tax_rate": 0.0,
                "tax_amount": 0.0,
                "note": "Stub inicial; cálculo real ainda pendente.",
            }
        ],
        "calculated_at": _sefaz_sp_now_iso(),
    }


def _sefaz_sp_build_xml(invoice: Invoice, invoice_number: str, invoice_series: str, access_key: str) -> dict:
    return {
        "format": "xml_stub",
        "country": "BR",
        "authority": "SEFAZ-SP",
        "invoice_type": invoice.invoice_type,
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "order_id": invoice.order_id,
        "generated_at": _sefaz_sp_now_iso(),
        "xml_preview": (
            f"<NFe>"
            f"<infNFe Id='{access_key}'>"
            f"<ide><nNF>{invoice_number}</nNF><serie>{invoice_series}</serie></ide>"
            f"<emit><xNome>ELLAN STUB SP</xNome></emit>"
            f"<dest><xNome>CLIENTE FINAL</xNome></dest>"
            f"</infNFe>"
            f"</NFe>"
        ),
    }


def _sefaz_sp_build_government_response(invoice: Invoice, invoice_number: str, invoice_series: str, access_key: str) -> dict:
    return {
        "provider_namespace": "sefaz_sp",
        "provider_status": "AUTHORIZED",
        "provider_code": "100",
        "provider_message": "Autorizado o uso da NF-e (stub).",
        "receipt_number": f"sefaz_sp_rec_{uuid.uuid4().hex[:20]}",
        "protocol_number": f"sefaz_sp_prot_{uuid.uuid4().hex[:20]}",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "processed_at": _sefaz_sp_now_iso(),
        "raw": {
            "environment": "stub",
            "state": "SP",
            "integration_mode": "local_stub",
        },
    }


def sefaz_sp_issue_invoice(invoice: Invoice) -> dict:
    invoice_number = _sefaz_sp_generate_invoice_number(invoice)
    invoice_series = _sefaz_sp_generate_series()
    access_key = _sefaz_sp_generate_access_key(invoice)

    tax_details = _sefaz_sp_build_tax_details(invoice)
    xml_content = _sefaz_sp_build_xml(invoice, invoice_number, invoice_series, access_key)
    government_response = _sefaz_sp_build_government_response(
        invoice, invoice_number, invoice_series, access_key
    )

    return {
        "provider": "sefaz_sp",
        "country": "BR",
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": tax_details,
        "xml_content": xml_content,
        "government_response": government_response,
    }
    