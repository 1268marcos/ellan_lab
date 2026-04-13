# 01_source/payment_gateway/app/schemas/payment.py
# Modelo de Request para o Endpoint

from pydantic import BaseModel, Field
from typing import Literal, Optional


class CancelPaymentRequest(BaseModel):
    """Request model para cancelamento de pagamento"""
    reason: Literal["user_requested", "duplicate", "fraud_suspicion", "timeout"] = Field(
        ..., 
        description="Motivo do cancelamento"
    )
    requested_by: Literal["customer", "merchant", "system"] = Field(
        ..., 
        description="Quem solicitou o cancelamento"
    )
    amount: Optional[float] = Field(
        None, 
        description="Valor para reembolso parcial (se None, reembolsa total)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "user_requested",
                "requested_by": "customer",
                "amount": 10022
            }
        }