class PaymentProviderError(Exception):
    pass


class PaymentAuthenticationError(PaymentProviderError):
    pass


class PaymentValidationError(PaymentProviderError):
    pass


class PaymentWebhookVerificationError(PaymentProviderError):
    pass
