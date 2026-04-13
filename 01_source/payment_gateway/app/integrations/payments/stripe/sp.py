# 01_source/payment_gateway/app/integrations/payments/stripe/sp.py


from app.integrations.payments.stripe.client import StripeClient


def build_provider(secret_key: str) -> StripeClient:
    return StripeClient(secret_key=secret_key, account_region="SP")
