# 01_source/backend/billing_fiscal_service/app/services/fiscal_router_service.py
from __future__ import annotations

from app.models.invoice_model import Invoice
from app.services.aeat_es_service import aeat_es_issue_invoice
from app.services.at_pt_service import at_pt_issue_invoice
from app.services.sefaz_sp_service import sefaz_sp_issue_invoice


def route_issue_invoice(invoice: Invoice) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        return sefaz_sp_issue_invoice(invoice)

    if country == "PT":
        return at_pt_issue_invoice(invoice)

    if country == "ES":
        return aeat_es_issue_invoice(invoice)

    raise ValueError(f"País não suportado para emissão fiscal: {country}")
