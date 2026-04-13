# 01_source/payment_gateway/app/models/cancel_payment_model.py
# 12/04/2026

from pydantic import BaseModel

class CancelPaymentRequest(BaseModel):
    reason: str
    requested_by: str | None = None