# 01_source/backend/billing_fiscal_service/app/services/sefaz_sp_service.py
# (stub)
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.invoice_model import Invoice

from app.core.datetime_utils import to_iso_utc



def _sefaz_sp_now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))


def _sefaz_sp_generate_invoice_number(invoice: Invoice) -> str:
    suffix = str(invoice.id)[-6:].upper()
    return f"SP{datetime.now(timezone.utc).strftime('%Y%m%d')}{suffix}"


def _sefaz_sp_generate_series() -> str:
    return "SP-1"


def _sefaz_sp_generate_access_key(invoice: Invoice) -> str:
    return f"sefaz_sp_{uuid.uuid4().hex}"


def _sefaz_sp_build_tax_details(invoice: Invoice) -> dict:
    amount_cents = invoice.amount_cents or 0
    amount = round(amount_cents / 100, 2)
    tb = invoice.tax_breakdown_json or {}
    lines = tb.get("lines") or []
    summary = tb.get("summary") or {}

    taxes: list[dict] = []
    if lines:
        tot_icms = sum(int(x.get("icms_cents") or 0) for x in lines)
        tot_pis = sum(int(x.get("pis_cents") or 0) for x in lines)
        tot_cof = sum(int(x.get("cofins_cents") or 0) for x in lines)
        base = int(summary.get("total_taxable_cents") or amount_cents)
        if tot_icms:
            taxes.append(
                {
                    "tax_type": "ICMS",
                    "tax_rate": round(tot_icms / max(base, 1), 6),
                    "tax_amount": round(tot_icms / 100, 2),
                    "amount_cents": tot_icms,
                }
            )
        if tot_pis:
            taxes.append(
                {
                    "tax_type": "PIS",
                    "tax_rate": 0.0065,
                    "tax_amount": round(tot_pis / 100, 2),
                    "amount_cents": tot_pis,
                }
            )
        if tot_cof:
            taxes.append(
                {
                    "tax_type": "COFINS",
                    "tax_rate": 0.03,
                    "tax_amount": round(tot_cof / 100, 2),
                    "amount_cents": tot_cof,
                }
            )
    if not taxes:
        taxes.append(
            {
                "tax_type": "ICMS",
                "tax_rate": 0.0,
                "tax_amount": 0.0,
                "note": "Sem linhas de imposto calculadas.",
            }
        )

    regime = "simples_nacional" if tb.get("regime_simples_nacional") else "normal"

    return {
        "country": "BR",
        "authority": "SEFAZ-SP",
        "provider_namespace": "sefaz_sp",
        "regime": regime,
        "base_amount_cents": amount_cents,
        "base_amount": amount,
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
        "taxes": taxes,
        "breakdown_lines": lines,
        "calculated_at": _sefaz_sp_now_iso(),
    }


def _sefaz_sp_build_xml(invoice: Invoice, invoice_number: str, invoice_series: str, access_key: str) -> dict:
    snapshot = invoice.order_snapshot or {}
    order = snapshot.get("order") or {}
    pickup = snapshot.get("pickup") or {}

    locker_id = invoice.locker_id or pickup.get("locker_id")
    slot = invoice.slot_label if invoice.slot_label is not None else pickup.get("slot")
    emit_name = invoice.emitter_name or "ELLAN STUB SP"
    dest_name = invoice.consumer_name or "CLIENTE FINAL"
    fiscal_subtype = invoice.fiscal_doc_subtype or "NFC_E_65"

    return {
        "format": "xml_stub",
        "country": "BR",
        "authority": "SEFAZ-SP",
        "provider_namespace": "sefaz_sp",
        "invoice_type": invoice.invoice_type,
        "fiscal_doc_subtype": fiscal_subtype,
        "emission_mode": invoice.emission_mode,
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "order_id": invoice.order_id,
        "region": invoice.region,
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
        "amount_cents": invoice.amount_cents,
        "locker_id": locker_id,
        "totem_id": invoice.totem_id,
        "slot": slot,
        "emitter_cnpj": invoice.emitter_cnpj,
        "consumer_cpf": invoice.consumer_cpf,
        "locker_address": invoice.locker_address,
        "items_json": invoice.items_json,
        "generated_at": _sefaz_sp_now_iso(),
        "xml_preview": (
            f"<NFe>"
            f"<infNFe Id='{access_key}'>"
            f"<ide><nNF>{invoice_number}</nNF><serie>{invoice_series}</serie></ide>"
            f"<emit><xNome>{emit_name}</xNome></emit>"
            f"<dest><xNome>{dest_name}</xNome></dest>"
            f"<det><prod><cProd>{order.get('sku_id')}</cProd></prod></det>"
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
        "country": invoice.country,
        "region": invoice.region,
        "processed_at": _sefaz_sp_now_iso(),
        "raw": {
            "environment": "stub",
            "state": "SP",
            "integration_mode": "local_stub",
            "order_id": invoice.order_id,
            "amount_cents": invoice.amount_cents,
            "currency": invoice.currency,
            "payment_method": invoice.payment_method,
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