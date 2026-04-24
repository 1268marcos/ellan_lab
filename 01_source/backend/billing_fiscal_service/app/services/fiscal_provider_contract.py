from __future__ import annotations

from app.models.invoice_model import Invoice


def build_issue_payload(*, invoice: Invoice, country: str) -> dict:
    payload_json = invoice.payload_json if isinstance(invoice.payload_json, dict) else {}
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "region": invoice.region,
        "amount_cents": int(invoice.amount_cents or 0),
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
        "tax_breakdown_json": invoice.tax_breakdown_json,
        "order_snapshot": invoice.order_snapshot,
        # STUB controls for provider simulation (non-production fields)
        "stub_scenario": payload_json.get("stub_scenario"),
        "stub_success_on_attempt": payload_json.get("stub_success_on_attempt"),
        "stub_batch_poll_count": payload_json.get("stub_batch_poll_count"),
        "ready_after_polls": payload_json.get("ready_after_polls"),
        "idempotency_key": payload_json.get("idempotency_key"),
    }


def build_cancel_payload(*, invoice: Invoice, country: str) -> dict:
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "access_key": invoice.access_key,
    }


def build_correction_payload(*, invoice: Invoice, country: str, correction_text: str | None) -> dict:
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "access_key": invoice.access_key,
        "correction_text": correction_text,
    }


def normalize_issue_response(*, invoice: Invoice, country: str, provider: str, raw: dict) -> dict:
    if country == "BR":
        invoice_number = raw.get("invoice_number") or raw.get("number") or f"SVRS-{invoice.id[-6:]}"
        invoice_series = raw.get("invoice_series") or raw.get("series") or "SVRS-1"
        access_key = raw.get("access_key") or raw.get("chave") or invoice.access_key
        status = "AUTHORIZED"
        code = "100"
        message = "Autorizado."
        xml_default = {"format": "xml_real_provider"}
    else:
        invoice_number = raw.get("invoice_number") or raw.get("number") or f"AT-{invoice.id[-6:]}"
        invoice_series = raw.get("invoice_series") or raw.get("series") or "AT-1"
        access_key = raw.get("access_key") or raw.get("hash") or invoice.access_key
        status = "ACCEPTED"
        code = "AT-200"
        message = "Documento aceite."
        xml_default = {"format": "saft_real_provider"}

    gov = raw.get("government_response") if isinstance(raw.get("government_response"), dict) else {}
    if not gov:
        gov = {
            "provider_namespace": provider,
            "provider_status": str(raw.get("provider_status") or raw.get("status") or status),
            "provider_code": str(raw.get("provider_code") or raw.get("code") or code),
            "provider_message": str(raw.get("provider_message") or raw.get("message") or message),
            "receipt_number": raw.get("receipt_number"),
            "protocol_number": raw.get("protocol_number"),
            "raw": raw,
        }

    return {
        "provider": provider,
        "country": country,
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": raw.get("tax_details") or invoice.tax_details or {},
        "xml_content": raw.get("xml_content") or invoice.xml_content or xml_default,
        "government_response": gov,
    }


def normalize_cancel_response(*, invoice: Invoice, country: str, provider: str, raw: dict) -> dict:
    return {
        "provider": provider,
        "country": country,
        "cancel_status": str(raw.get("cancel_status") or raw.get("status") or "CANCELLED"),
        "access_key": raw.get("access_key") or invoice.access_key,
        "protocol_number": raw.get("protocol_number"),
        "processed_at": raw.get("processed_at"),
        "raw": raw,
    }


def normalize_correction_response(
    *,
    invoice: Invoice,
    country: str,
    provider: str,
    correction_text: str | None,
    raw: dict,
) -> dict:
    response = {
        "provider": provider,
        "kind": "cce" if country == "BR" else "correction",
        "country": country,
        "access_key": raw.get("access_key") or invoice.access_key,
        "correction_text": str(raw.get("correction_text") or correction_text or "")[:1000],
        "protocol_number": raw.get("protocol_number"),
        "processed_at": raw.get("processed_at"),
        "raw": raw,
    }
    if country == "BR":
        response["sequence"] = int(raw.get("sequence") or 1)
        response["xml_event_preview"] = raw.get("xml_event_preview")
    return response
