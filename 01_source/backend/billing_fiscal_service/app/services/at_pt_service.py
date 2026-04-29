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


def _at_pt_build_raw(invoice: Invoice, *, operation: str, extra: dict | None = None) -> dict:
    payload = {
        "contract_version": "f3_stub_canonical_v1",
        "provider_namespace": "at_pt_stub",
        "provider_mode": "stub_dedicated",
        "integration_mode": "local_stub",
        "operation": operation,
        "order_id": invoice.order_id,
        "invoice_id": invoice.id,
        "country": "PT",
        "region": invoice.region,
        "amount_cents": int(invoice.amount_cents or 0),
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
    }
    if extra:
        payload.update(extra)
    return payload


def at_pt_issue_invoice(invoice: Invoice) -> dict:
    invoice_number = _at_pt_generate_invoice_number(invoice)
    invoice_series = _at_pt_generate_series()
    access_key = _at_pt_generate_access_key(invoice)

    tb = invoice.tax_breakdown_json or {}
    lines = tb.get("lines") or []
    summary = tb.get("summary") or {}
    tot_iva = sum(int(x.get("iva_cents") or 0) for x in lines)
    base = int(summary.get("total_taxable_cents") or invoice.amount_cents or 0)
    iva_rate = round(tot_iva / max(base, 1), 6) if tot_iva and base else 0.0

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
                    "tax_rate": iva_rate,
                    "tax_amount": round(tot_iva / 100, 2),
                    "amount_cents": tot_iva,
                    "note": "Motor F-2 (tax_service).",
                }
            ],
            "breakdown_lines": lines,
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
            "provider_namespace": "at_pt_stub",
            "provider_status": "ACCEPTED",
            "provider_code": "AT-200",
            "provider_message": "Documento fiscal aceite pela AT (stub).",
            "receipt_number": f"at_pt_rec_{uuid.uuid4().hex[:20]}",
            "protocol_number": f"at_pt_prot_{uuid.uuid4().hex[:20]}",
            "invoice_number": invoice_number,
            "invoice_series": invoice_series,
            "access_key": access_key,
            "processed_at": _at_pt_now_iso(),
            "raw": _at_pt_build_raw(invoice, operation="ISSUE"),
        },
    }


def at_pt_cc_e_stub(invoice: Invoice, correction_text: str | None) -> dict:
    """Stub análogo a CC-e para PT (integração AT em F-3)."""
    text = (correction_text or "").strip() or "Correção documental (stub)."
    return {
        "provider": "at_pt",
        "kind": "correction",
        "country": "PT",
        "access_key": invoice.access_key or _at_pt_generate_access_key(invoice),
        "correction_text": text[:1000],
        "protocol_number": f"at_pt_corr_{uuid.uuid4().hex[:18]}",
        "processed_at": _at_pt_now_iso(),
        "raw": _at_pt_build_raw(
            invoice,
            operation="CORRECTION",
            extra={"correction_text": text[:1000]},
        ),
    }


def at_pt_cancel_invoice(invoice: Invoice) -> dict:
    """Stub I-2 — anular documento PT (integração AT real em F-3)."""
    return {
        "provider": "at_pt",
        "country": "PT",
        "cancel_status": "CANCELLED",
        "access_key": invoice.access_key or _at_pt_generate_access_key(invoice),
        "protocol_number": f"at_pt_cancel_{uuid.uuid4().hex[:20]}",
        "processed_at": _at_pt_now_iso(),
        "raw": _at_pt_build_raw(invoice, operation="CANCEL"),
    }
