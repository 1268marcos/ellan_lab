from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.finance import FinancePartnerAccount, PartnerB2bInvoice
from app.models.finance_advanced import PartnerInvoiceDocument
from app.services.billing_fiscal_client import BillingFiscalClientError, is_fiscal_live_enabled, issue_partner_b2b_fiscal
from app.services.crypto_util import new_id
from app.services.finance_audit_service import log_audit


def emit_b2b_invoice_fiscal(db: Session, invoice_id: str) -> dict:
    inv = db.get(PartnerB2bInvoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.fiscal_status == "AUTHORIZED":
        return {
            "invoice_id": invoice_id,
            "fiscal_status": inv.fiscal_status,
            "access_key": inv.fiscal_access_key,
            "pdf_url": inv.fiscal_pdf_url,
            "already_issued": True,
        }

    partner = db.get(FinancePartnerAccount, inv.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    if not is_fiscal_live_enabled():
        inv.fiscal_status = "STUB_AUTHORIZED"
        inv.fiscal_access_key = f"STUB{invoice_id.replace('-', '')[:40]}"
        inv.fiscal_pdf_url = f"https://fiscal.ellanlab.example/stub/b2b/{invoice_id}.pdf"
        inv.status = "ISSUED"
        if not db.query(PartnerInvoiceDocument).filter(PartnerInvoiceDocument.invoice_id == invoice_id).first():
            db.add(
                PartnerInvoiceDocument(
                    id=new_id(),
                    invoice_id=invoice_id,
                    document_kind="PDF",
                    storage_uri=inv.fiscal_pdf_url,
                    access_key=inv.fiscal_access_key,
                    fiscal_invoice_id=invoice_id,
                    country=partner.country_code or "BR",
                    issued_at=inv.issued_at,
                )
            )
        log_audit(db, action="EMIT_FISCAL_STUB", entity_type="b2b_invoice", entity_id=invoice_id)
        db.commit()
        return {
            "invoice_id": invoice_id,
            "fiscal_status": inv.fiscal_status,
            "access_key": inv.fiscal_access_key,
            "pdf_url": inv.fiscal_pdf_url,
            "mode": "STUB",
        }

    try:
        payload = issue_partner_b2b_fiscal(partner_id=inv.partner_id, invoice_id=invoice_id)
    except BillingFiscalClientError as exc:
        inv.fiscal_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    inv.fiscal_status = "AUTHORIZED"
    inv.fiscal_access_key = payload.get("access_key")
    inv.fiscal_pdf_url = payload.get("pdf_url")
    inv.status = "ISSUED"
    if not db.query(PartnerInvoiceDocument).filter(PartnerInvoiceDocument.invoice_id == invoice_id).first():
        db.add(
            PartnerInvoiceDocument(
                id=new_id(),
                invoice_id=invoice_id,
                document_kind="PDF",
                storage_uri=inv.fiscal_pdf_url,
                access_key=inv.fiscal_access_key,
                fiscal_invoice_id=invoice_id,
                country=payload.get("country_code") or partner.country_code or "BR",
            )
        )
    log_audit(
        db,
        action="EMIT_FISCAL_LIVE",
        entity_type="b2b_invoice",
        entity_id=invoice_id,
        after=payload,
    )
    db.commit()
    return {"invoice_id": invoice_id, "mode": "LIVE", **payload}
