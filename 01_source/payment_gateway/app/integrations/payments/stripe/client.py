from app.integrations.payments.base.contracts import CreatePaymentCommand, PaymentResult


class StripeClient:
    provider_name = "stripe"

    def __init__(self, secret_key: str, account_region: str) -> None:
        self.secret_key = secret_key
        self.account_region = account_region

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"stripe_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
