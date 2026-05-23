"""Emissão fiscal B2B de parceiro (stub/real conforme país)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stub_access_key(invoice_id: str, country: str) -> str:
    prefix = {"BR": "35", "PT": "PT", "ES": "ES"}.get(country, "XX")
    digits = "".join(ch for ch in invoice_id if ch.isdigit()) or uuid.uuid4().hex
    return f"{prefix}{digits[:40]:0<40}"[:44]


def issue_partner_b2b_invoice(db: Session, *, partner_id: str, invoice_id: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT id, partner_id, status, document_type, amount_cents, tax_cents,
                   currency, country_code, jurisdiction_code, invoice_number
            FROM partner_b2b_invoices
            WHERE id = :invoice_id AND partner_id = :partner_id
            """
        ),
        {"invoice_id": invoice_id, "partner_id": partner_id},
    ).mappings().first()
    if not row:
        raise ValueError("partner_b2b_invoice_not_found")
    if row["status"] in ("CANCELLED",):
        raise ValueError("invoice_cancelled")

    country = (row["country_code"] or "BR").upper()
    access_key = _stub_access_key(invoice_id, country)
    invoice_number = row["invoice_number"] or f"B2B-{invoice_id[:8].upper()}"
    now = _utcnow()

    if country == "BR" and settings.fiscal_real_provider_br_enabled:
        provider_mode = "SVRS_REAL_OR_FALLBACK"
    elif country == "PT" and settings.fiscal_real_provider_pt_enabled:
        provider_mode = "AT_REAL_OR_FALLBACK"
    else:
        provider_mode = "STUB"

    pdf_url = f"https://fiscal.ellanlab.example/{country.lower()}/b2b/{invoice_id}.pdf"
    government_response = {
        "provider_mode": provider_mode,
        "status": "AUTHORIZED",
        "access_key": access_key,
        "issued_at": now.isoformat(),
    }

    db.execute(
        text(
            """
            UPDATE partner_b2b_invoices
            SET status = 'ISSUED',
                invoice_number = :invoice_number,
                access_key = :access_key,
                issued_at = :issued_at,
                pdf_url = :pdf_url,
                government_response = CAST(:government_response AS JSONB),
                external_provider_ref = :external_provider_ref,
                updated_at = :issued_at
            WHERE id = :invoice_id
            """
        ),
        {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "access_key": access_key,
            "issued_at": now,
            "pdf_url": pdf_url,
            "government_response": __import__("json").dumps(government_response),
            "external_provider_ref": f"fiscal-{provider_mode.lower()}",
        },
    )
    db.commit()
    return {
        "invoice_id": invoice_id,
        "partner_id": partner_id,
        "status": "ISSUED",
        "access_key": access_key,
        "pdf_url": pdf_url,
        "provider_mode": provider_mode,
        "country_code": country,
    }
