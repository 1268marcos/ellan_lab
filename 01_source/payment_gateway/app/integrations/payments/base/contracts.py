from dataclasses import dataclass
from typing import Protocol


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


class PaymentProvider(Protocol):
    provider_name: str

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        ...

    def get_payment_status(self, provider_payment_id: str) -> PaymentResult:
        ...
