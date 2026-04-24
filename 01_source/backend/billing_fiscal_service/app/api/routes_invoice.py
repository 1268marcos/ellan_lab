# 01_source/backend/billing_fiscal_service/app/api/routes_invoice.py
# 01_source/backend/billing_fiscal_service/app/routers/internal_invoices.py (NUNCA FOI CRIADO)
# 19/04/2026 - datetime

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.invoice_model import Invoice, InvoiceStatus
from app.schemas.invoice_schema import CancelRequestIn, CcRequestIn, InvoiceResponse

# from app.services.invoice_issue_service import reset_invoice_for_retry
# from app.services.invoice_service import generate_invoice
from app.services.invoice_issue_service import reset_invoice_for_retry
from app.services.invoice_cancel_service import request_invoice_cancel
from app.services.invoice_orchestrator import ensure_and_process_invoice

from app.core.datetime_utils import to_iso_utc



router = APIRouter(prefix="/internal/invoices", tags=["invoices"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _iso_or_none(value):
    return to_iso_utc(value)


def _derive_previous_receipt_code(invoice: Invoice) -> str | None:
    """
    Referência do comprovante anterior para reemissão.
    Prioridade: protocolo fiscal > access_key > número/série.
    """
    gr = invoice.government_response or {}
    if isinstance(gr, dict):
        protocol = gr.get("protocol_number")
        if protocol:
            return str(protocol)
    if invoice.access_key:
        return str(invoice.access_key)
    if invoice.invoice_number and invoice.invoice_series:
        return f"{invoice.invoice_series}-{invoice.invoice_number}"
    if invoice.invoice_number:
        return str(invoice.invoice_number)
    return None


def _to_invoice_response(invoice: Invoice) -> InvoiceResponse:
    pj = invoice.payload_json or {}
    previous_receipt_code = None
    if isinstance(pj, dict):
        previous_receipt_code = pj.get("previous_receipt_code")
    return InvoiceResponse(
        id=invoice.id,
        order_id=invoice.order_id,
        tenant_id=invoice.tenant_id,
        region=invoice.region,
        country=invoice.country,
        invoice_type=invoice.invoice_type,
        payment_method=invoice.payment_method,
        currency=invoice.currency,
        amount_cents=invoice.amount_cents,
        status=str(getattr(invoice.status, "value", invoice.status)),
        retry_count=int(invoice.retry_count or 0),
        next_retry_at=_iso_or_none(invoice.next_retry_at),
        issued_at=_iso_or_none(invoice.issued_at),
        created_at=_iso_or_none(invoice.created_at),
        updated_at=_iso_or_none(invoice.updated_at),
        invoice_number=invoice.invoice_number,
        invoice_series=invoice.invoice_series,
        access_key=invoice.access_key,
        error_message=invoice.error_message,
        last_error_code=invoice.last_error_code,
        government_response=invoice.government_response,
        tax_details=invoice.tax_details,
        tax_breakdown_json=invoice.tax_breakdown_json,
        xml_content=invoice.xml_content,
        order_snapshot=invoice.order_snapshot,
        locker_id=invoice.locker_id,
        totem_id=invoice.totem_id,
        slot_label=invoice.slot_label,
        fiscal_doc_subtype=invoice.fiscal_doc_subtype,
        emission_mode=invoice.emission_mode,
        emitter_cnpj=invoice.emitter_cnpj,
        emitter_name=invoice.emitter_name,
        consumer_cpf=invoice.consumer_cpf,
        consumer_name=invoice.consumer_name,
        locker_address=invoice.locker_address,
        items_json=invoice.items_json,
        previous_receipt_code=previous_receipt_code,
    )


@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def create_invoice(
    order_id: str,
    allow_missing_paid_event: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    try:
        invoice = ensure_and_process_invoice(
            db,
            order_id,
            allow_missing_paid_event=allow_missing_paid_event,
        )
        return _to_invoice_response(invoice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _to_invoice_response(invoice)


@router.get("/by-order/{order_id}", response_model=InvoiceResponse)
def get_invoice_by_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for order")
    return _to_invoice_response(invoice)


@router.post("/{invoice_id}/retry", response_model=InvoiceResponse)
def retry_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = reset_invoice_for_retry(db, invoice, clear_identifiers=False)
    return _to_invoice_response(invoice)


@router.post("/{invoice_id}/cce-request", response_model=InvoiceResponse)
def request_cce_stub_queue(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
    body: CcRequestIn | None = Body(default=None),
):
    """
    Enfileira correção (CC-e stub): ISSUED → CORRECTION_REQUESTED.
    O worker aplica `route_cc_e_stub` e volta para ISSUED com `cce_events` no government_response.
    """
    payload = body or CcRequestIn()
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status != InvoiceStatus.ISSUED:
        raise HTTPException(
            status_code=400,
            detail=f"Apenas invoice ISSUED pode solicitar CC-e; status={inv.status.value}",
        )
    pj = dict(inv.payload_json or {})
    pj["cce_manual_request"] = {
        "correction_text": (payload.correction_text or "").strip() or None,
        "requested_at": to_iso_utc(datetime.now(timezone.utc)),
    }
    inv.payload_json = pj
    inv.status = InvoiceStatus.CORRECTION_REQUESTED
    inv.next_retry_at = None
    inv.error_message = None
    inv.last_error_code = None
    db.commit()
    db.refresh(inv)
    return _to_invoice_response(inv)


@router.post("/{invoice_id}/cancel-request", response_model=InvoiceResponse)
def request_cancel_invoice_endpoint(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
    body: CancelRequestIn | None = Body(default=None),
):
    """
    I-2: solicita cancelamento conforme política (void / CC-e / complemento — stub SEFAZ no worker).
    """
    payload = body or CancelRequestIn()
    try:
        inv = request_invoice_cancel(
            db,
            invoice_id=invoice_id,
            reason=payload.reason,
            source=payload.source or "api",
        )
        return _to_invoice_response(inv)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{invoice_id}/reissue", response_model=InvoiceResponse)
def reissue_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    prev_code = _derive_previous_receipt_code(invoice)
    if prev_code:
        pj = dict(invoice.payload_json or {})
        pj["previous_receipt_code"] = prev_code
        pj["reissue_requested_at"] = to_iso_utc(datetime.now(timezone.utc))
        invoice.payload_json = pj
        db.commit()
        db.refresh(invoice)

    invoice = reset_invoice_for_retry(db, invoice, clear_identifiers=True)
    return _to_invoice_response(invoice)