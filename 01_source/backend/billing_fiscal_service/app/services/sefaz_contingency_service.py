from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.invoice_model import Invoice


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def issue_invoice_contingency_stub(invoice: Invoice) -> dict:
    """
    F-3 slice: emissão em contingência SAT/MFe offline.
    O documento é aceito internamente e marcado para sincronização posterior.
    """
    mode = str(invoice.emission_mode or "").strip().upper()
    if mode not in {"OFFLINE_SAT", "CONTINGENCY_SVRS"}:
        raise ValueError(f"emission_mode inválido para contingência: {mode}")

    suffix = str(invoice.id)[-6:].upper()
    invoice_number = f"CTG{datetime.now(timezone.utc).strftime('%Y%m%d')}{suffix}"
    invoice_series = "SAT-1" if mode == "OFFLINE_SAT" else "SVRS-CONT-1"
    access_key = invoice.access_key or f"cont_{uuid.uuid4().hex}"
    sync_id = f"sync_{uuid.uuid4().hex[:20]}"

    gov = {
        "provider_namespace": "sefaz_contingency",
        "provider_status": "CONTINGENCY_PENDING_SYNC",
        "provider_code": "PEND_SYNC",
        "provider_message": "Emitido em contingência; pendente sincronização com autoridade.",
        "protocol_number": None,
        "receipt_number": None,
        "sync_pending": True,
        "sync_id": sync_id,
        "sync_state": "PENDING",
        "processed_at": _now_iso(),
        "raw": {
            "integration_mode": "contingency_stub",
            "emission_mode": mode,
            "order_id": invoice.order_id,
            "country": invoice.country,
        },
    }

    return {
        "provider": "sefaz_contingency",
        "country": "BR",
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": invoice.tax_details or {},
        "xml_content": {
            "format": "xml_contingency_stub",
            "emission_mode": mode,
            "sync_id": sync_id,
            "generated_at": _now_iso(),
        },
        "government_response": gov,
    }
