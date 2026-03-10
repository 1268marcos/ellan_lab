from app.integrations.payments.base.contracts import CreatePaymentCommand, PaymentResult


class MercadoPagoClient:
    provider_name = "mercadopago"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"mp_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
