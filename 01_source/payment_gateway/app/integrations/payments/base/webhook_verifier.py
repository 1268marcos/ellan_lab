# 01_source/payment_gateway/app/integrations/payments/base/webhook_verifier.py


from shared_kernel.security.webhook_signatures import verify_hmac_sha256
from app.integrations.payments.base.exceptions import PaymentWebhookVerificationError


def verify_webhook_or_raise(payload: bytes, secret: str, received_signature: str) -> None:
    valid = verify_hmac_sha256(payload, secret, received_signature)
    if not valid:
        raise PaymentWebhookVerificationError("Invalid webhook signature")
