# 01_source/backend/billing_fiscal_service/app/schemas/invoice_schema.py
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    id: str
    order_id: str
    status: str