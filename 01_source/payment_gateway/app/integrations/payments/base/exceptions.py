# 01_source/payment_gateway/app/integrations/payments/base/exceptions.py


class PaymentProviderError(Exception):
    pass


class PaymentAuthenticationError(PaymentProviderError):
    pass


class PaymentValidationError(PaymentProviderError):
    pass


class PaymentWebhookVerificationError(PaymentProviderError):
    pass
