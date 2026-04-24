# 01_source/backend/billing_fiscal_service/app/services/fiscal_router_service.py
from __future__ import annotations

from app.core.config import settings
from app.models.invoice_model import Invoice
from app.services.aeat_es_service import (
    aeat_es_cancel_invoice,
    aeat_es_cc_e_stub,
    aeat_es_issue_invoice,
)
from app.services.at_pt_real_adapter import (
    cancel_invoice_real_or_fallback as at_cancel_real_or_fallback,
    correction_event_real_or_fallback as at_correction_real_or_fallback,
    issue_invoice_real_or_fallback as at_issue_real_or_fallback,
)
from app.services.at_pt_service import at_pt_cancel_invoice, at_pt_cc_e_stub, at_pt_issue_invoice
from app.services.sefaz_sp_service import sefaz_sp_cancel_invoice, sefaz_sp_cc_e_stub, sefaz_sp_issue_invoice
from app.services.sefaz_svrs_real_adapter import (
    cancel_invoice_real_or_fallback as svrs_cancel_real_or_fallback,
    cce_event_real_or_fallback as svrs_cce_real_or_fallback,
    issue_invoice_real_or_fallback as svrs_issue_real_or_fallback,
)


def route_issue_invoice(invoice: Invoice) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_issue_real_or_fallback(invoice)
        return sefaz_sp_issue_invoice(invoice)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_issue_real_or_fallback(invoice)
        return at_pt_issue_invoice(invoice)

    if country == "ES":
        return aeat_es_issue_invoice(invoice)

    raise ValueError(f"País não suportado para emissão fiscal: {country}")


def route_cancel_invoice(invoice: Invoice) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_cancel_real_or_fallback(invoice)
        return sefaz_sp_cancel_invoice(invoice)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_cancel_real_or_fallback(invoice)
        return at_pt_cancel_invoice(invoice)

    if country == "ES":
        return aeat_es_cancel_invoice(invoice)

    raise ValueError(f"País não suportado para cancelamento fiscal: {country}")


def route_cc_e_stub(invoice: Invoice, correction_text: str | None) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_cce_real_or_fallback(invoice, correction_text)
        return sefaz_sp_cc_e_stub(invoice, correction_text)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_correction_real_or_fallback(invoice, correction_text)
        return at_pt_cc_e_stub(invoice, correction_text)

    if country == "ES":
        return aeat_es_cc_e_stub(invoice, correction_text)

    raise ValueError(f"País não suportado para CC-e / correção fiscal: {country}")
