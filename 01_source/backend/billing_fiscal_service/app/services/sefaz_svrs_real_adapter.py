from __future__ import annotations

import logging

from app.integrations.fiscal_real_provider_client import RealProviderClientError
from app.integrations.fiscal_real_provider_client import cancel_invoice as provider_cancel_invoice
from app.integrations.fiscal_real_provider_client import correction_event as provider_correction_event
from app.integrations.fiscal_real_provider_client import issue_invoice as provider_issue_invoice
from app.models.invoice_model import Invoice
from app.services.fiscal_provider_contract import (
    build_cancel_payload,
    build_correction_payload,
    build_issue_payload,
    normalize_cancel_response,
    normalize_correction_response,
    normalize_issue_response,
)
from app.services.sefaz_sp_service import (
    sefaz_sp_cancel_invoice,
    sefaz_sp_cc_e_stub,
    sefaz_sp_issue_invoice,
)

logger = logging.getLogger(__name__)


def issue_invoice_real_or_fallback(invoice: Invoice) -> dict:
    """
    Slice F-3: ponto único para integrar SVRS/SEFAZ real.
    Enquanto o client oficial não está plugado, mantém fallback para stub atual.
    """
    try:
        raw = provider_issue_invoice("BR", build_issue_payload(invoice=invoice, country="BR"))
        return normalize_issue_response(
            invoice=invoice,
            country="BR",
            provider="svrs_real",
            raw=raw,
        )
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_svrs_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = sefaz_sp_issue_invoice(invoice)
        gr = dict(out.get("government_response") or {})
        rw = dict(gr.get("raw") or {})
        rw["provider_adapter"] = "svrs_real_adapter_fallback"
        rw["fallback_reason"] = str(exc)
        gr["raw"] = rw
        out["government_response"] = gr
        return out


def cancel_invoice_real_or_fallback(invoice: Invoice) -> dict:
    try:
        raw = provider_cancel_invoice("BR", build_cancel_payload(invoice=invoice, country="BR"))
        return normalize_cancel_response(
            invoice=invoice,
            country="BR",
            provider="svrs_real",
            raw=raw,
        )
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_svrs_cancel_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = sefaz_sp_cancel_invoice(invoice)
        raw = dict(out.get("raw") or {})
        raw["provider_adapter"] = "svrs_real_adapter_fallback"
        raw["fallback_reason"] = str(exc)
        out["raw"] = raw
        return out


def cce_event_real_or_fallback(invoice: Invoice, correction_text: str | None) -> dict:
    try:
        raw = provider_correction_event(
            "BR",
            build_correction_payload(invoice=invoice, country="BR", correction_text=correction_text),
        )
        return normalize_correction_response(
            invoice=invoice,
            country="BR",
            provider="svrs_real",
            correction_text=correction_text,
            raw=raw,
        )
    except RealProviderClientError as exc:
        logger.warning(
            "fiscal_provider_svrs_cce_real_failed_fallback_stub",
            extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "error": str(exc)},
        )
        out = sefaz_sp_cc_e_stub(invoice, correction_text)
        raw = dict(out.get("raw") or {})
        raw["provider_adapter"] = "svrs_real_adapter_fallback"
        raw["fallback_reason"] = str(exc)
        out["raw"] = raw
        return out
