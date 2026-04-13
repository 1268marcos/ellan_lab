# 01_source/payment_gateway/app/integrations/payments/base/contracts.py

from dataclasses import dataclass
from typing import Protocol, Optional
from datetime import datetime


@dataclass
class CreatePaymentCommand:
    order_id: str
    amount: float
    currency: str
    country: str
    customer_reference: str | None = None


@dataclass
class PaymentResult:
    provider: str
    provider_payment_id: str
    status: str
    raw_status: str
    redirect_url: str | None = None
    qr_code: str | None = None


@dataclass
class CancelPaymentCommand:
    """Comando para cancelamento/refund de pagamento"""
    provider_payment_id: str
    reason: str
    amount: Optional[float] = None


@dataclass
class CancelPaymentResult:
    """Resultado do cancelamento/refund"""
    success: bool
    provider: str
    refund_id: str
    status: str  # "CANCELLED", "REFUNDED", "FAILED"
    error: Optional[str] = None
    processed_at: Optional[datetime] = None


class PaymentProvider(Protocol):
    provider_name: str

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        ...

    def get_payment_status(self, provider_payment_id: str) -> PaymentResult:
        ...

    async def cancel_payment(self, command: CancelPaymentCommand) -> CancelPaymentResult:
        """
        Cancela/Reembolsa um pagamento existente.
        
        Args:
            command: Comando com provider_payment_id e reason
            
        Returns:
            CancelPaymentResult: Resultado do cancelamento
        """
        ...