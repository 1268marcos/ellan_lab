# 01_source/backend/billing_fiscal_service/app/schemas/invoice_schema.py
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    id: str
    order_id: str
    tenant_id: str | None = None
    region: str | None = None
    country: str
    invoice_type: str
    payment_method: str | None = None
    currency: str | None = None
    amount_cents: int | None = None
    status: str
    retry_count: int
    next_retry_at: str | None = None
    issued_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    invoice_number: str | None = None
    invoice_series: str | None = None
    access_key: str | None = None
    error_message: str | None = None
    last_error_code: str | None = None
    government_response: dict | None = None
    tax_details: dict | None = None
    xml_content: dict | None = None
    order_snapshot: dict | None = None
    # F-1
    locker_id: str | None = None
    totem_id: str | None = None
    slot_label: str | None = None
    fiscal_doc_subtype: str | None = None
    emission_mode: str | None = None
    emitter_cnpj: str | None = None
    emitter_name: str | None = None
    consumer_cpf: str | None = None
    consumer_name: str | None = None
    locker_address: dict | None = None
    items_json: dict | None = None