from __future__ import annotations

import logging

from app.integrations.fiscal_real_provider_client import RealProviderClientError
from app.integrations.fiscal_real_provider_client import cancel_invoice as provider_cancel_invoice
from app.integrations.fiscal_real_provider_client import correction_event as provider_correction_event
from app.integrations.fiscal_real_provider_client import issue_invoice as provider_issue_invoice
from app.models.invoice_model import Invoice
from app.services.at_pt_service import at_pt_cancel_invoice, at_pt_cc_e_stub, at_pt_issue_invoice

logger = logging.getLogger(__name__)


def _issue_payload(invoice: Invoice) -> dict:
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": "PT",
        "amount_cents": int(invoice.amount_cents or 0),
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
        "tax_breakdown_json": invoice.tax_breakdown_json,
        "order_snapshot": invoice.order_snapshot,
    }


def _normalize_issue_response(invoice: Invoice, raw: dict) -> dict:
    invoice_number = raw.get("invoice_number") or raw.get("number") or f"AT-{invoice.id[-6:]}"
    invoice_series = raw.get("invoice_series") or raw.get("series") or "AT-1"
    access_key = raw.get("access_key") or raw.get("hash") or invoice.access_key
    gov = raw.get("government_response") if isinstance(raw.get("government_response"), dict) else {}
    if not gov:
        gov = {
            "provider_namespace": "at_real",
            "provider_status": str(raw.get("provider_status") or raw.get("status") or "ACCEPTED"),
            "provider_code": str(raw.get("provider_code") or raw.get("code") or "AT-200"),
            "provider_message": str(raw.get("provider_message") or raw.get("message") or "Documento aceite."),
            "raw": raw,
        }
    return {
        "provider": "at_real",
        "country": "PT",
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": raw.get("tax_details") or invoice.tax_details or {},
        "xml_content": raw.get("xml_content") or invoice.xml_content or {"format": "saft_real_provider"},
        "government_response": gov,
    }


def issue_invoice_real_or_fallback(invoice: Invoice) -> dict:
    """
    Slice F-3: ponto único para integração AT real.
    Mantém fallback para provider stub até client oficial.
    """
    try:
        raw = provider_issue_invoice("PT", _issue_payload(invoice))
        return _normalize_issue_response(invoice, raw)
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_at_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = at_pt_issue_invoice(invoice)
        gr = dict(out.get("government_response") or {})
        rw = dict(gr.get("raw") or {})
        rw["provider_adapter"] = "at_real_adapter_fallback"
        rw["fallback_reason"] = str(exc)
        gr["raw"] = rw
        out["government_response"] = gr
        return out


def cancel_invoice_real_or_fallback(invoice: Invoice) -> dict:
    try:
        raw = provider_cancel_invoice(
            "PT",
            {
                "invoice_id": invoice.id,
                "order_id": invoice.order_id,
                "access_key": invoice.access_key,
            },
        )
        return {
            "provider": "at_real",
            "country": "PT",
            "cancel_status": str(raw.get("cancel_status") or raw.get("status") or "CANCELLED"),
            "access_key": raw.get("access_key") or invoice.access_key,
            "protocol_number": raw.get("protocol_number"),
            "processed_at": raw.get("processed_at"),
            "raw": raw,
        }
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_at_cancel_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = at_pt_cancel_invoice(invoice)
        raw = dict(out.get("raw") or {})
        raw["provider_adapter"] = "at_real_adapter_fallback"
        raw["fallback_reason"] = str(exc)
        out["raw"] = raw
        return out


def correction_event_real_or_fallback(invoice: Invoice, correction_text: str | None) -> dict:
    try:
        raw = provider_correction_event(
            "PT",
            {
                "invoice_id": invoice.id,
                "order_id": invoice.order_id,
                "access_key": invoice.access_key,
                "correction_text": correction_text,
            },
        )
        return {
            "provider": "at_real",
            "kind": "correction",
            "country": "PT",
            "access_key": raw.get("access_key") or invoice.access_key,
            "correction_text": str(raw.get("correction_text") or correction_text or "")[:1000],
            "protocol_number": raw.get("protocol_number"),
            "processed_at": raw.get("processed_at"),
            "raw": raw,
        }
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_at_correction_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = at_pt_cc_e_stub(invoice, correction_text)
        out["provider_adapter"] = "at_real_adapter_fallback"
        out["fallback_reason"] = str(exc)
        return out
