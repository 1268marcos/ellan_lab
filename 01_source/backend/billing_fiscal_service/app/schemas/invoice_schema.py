# 01_source/backend/billing_fiscal_service/app/schemas/invoice_schema.py
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    id: str
    order_id: str
    country: str
    invoice_type: str
    status: str
    invoice_number: str | None = None
    invoice_series: str | None = None
    access_key: str | None = None
    error_message: str | None = None