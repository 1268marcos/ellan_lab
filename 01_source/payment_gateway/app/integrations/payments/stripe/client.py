# 01_source/payment_gateway/app/integrations/payments/stripe/client.py

import stripe
from datetime import datetime
from app.integrations.payments.base.contracts import (
    CreatePaymentCommand,
    PaymentResult,
    CancelPaymentCommand,
    CancelPaymentResult
)


class StripeClient:
    provider_name = "stripe"

    def __init__(self, secret_key: str, account_region: str) -> None:
        self.secret_key = secret_key
        self.account_region = account_region
        stripe.api_key = secret_key

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        # Implementação existente...
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"stripe_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
    
    async def cancel_payment(self, command: CancelPaymentCommand) -> CancelPaymentResult:
        """
        Implementa cancelamento/refund no Stripe.
        
        Para Stripe:
        - PaymentIntents não capturados: Cancelamento via cancel()
        - PaymentIntents capturados: Refund via Refund.create()
        """
        try:
            # Obter PaymentIntent
            payment_intent = stripe.PaymentIntent.retrieve(command.provider_payment_id)
            
            if payment_intent.status == "requires_capture":
                # Cancelar PaymentIntent não capturado
                cancelled_intent = stripe.PaymentIntent.cancel(
                    command.provider_payment_id,
                    cancellation_reason=self._map_cancel_reason(command.reason)
                )
                
                return CancelPaymentResult(
                    success=True,
                    provider=self.provider_name,
                    refund_id=cancelled_intent.id,
                    status="CANCELLED",
                    processed_at=datetime.utcnow()
                )
                
            elif payment_intent.status == "succeeded":
                # Criar refund para pagamento capturado
                refund_params = {
                    "payment_intent": command.provider_payment_id,
                    "reason": self._map_refund_reason(command.reason)
                }
                
                if command.amount:
                    # Converter para centavos
                    refund_params["amount"] = int(command.amount * 100)
                
                refund = stripe.Refund.create(**refund_params)
                
                return CancelPaymentResult(
                    success=True,
                    provider=self.provider_name,
                    refund_id=refund.id,
                    status="REFUNDED",
                    processed_at=datetime.fromtimestamp(refund.created)
                )
                
            elif payment_intent.status in ["canceled", "refunded"]:
                return CancelPaymentResult(
                    success=False,
                    provider=self.provider_name,
                    refund_id="",
                    status="FAILED",
                    error=f"Payment already {payment_intent.status}: {command.provider_payment_id}"
                )
                
            else:
                return CancelPaymentResult(
                    success=False,
                    provider=self.provider_name,
                    refund_id="",
                    status="FAILED",
                    error=f"Cannot cancel payment with status: {payment_intent.status}"
                )
                
        except stripe.error.InvalidRequestError as e:
            return CancelPaymentResult(
                success=False,
                provider=self.provider_name,
                refund_id="",
                status="FAILED",
                error=f"Invalid request: {str(e)}"
            )
        except stripe.error.StripeError as e:
            return CancelPaymentResult(
                success=False,
                provider=self.provider_name,
                refund_id="",
                status="FAILED",
                error=f"Stripe API error: {str(e)}"
            )
    
    def _map_cancel_reason(self, reason: str) -> str:
        """Mapeia razão do cancelamento para Stripe"""
        mapping = {
            "user_requested": "requested_by_customer",
            "duplicate": "duplicate",
            "fraud_suspicion": "fraudulent"
        }
        return mapping.get(reason, "requested_by_customer")
    
    def _map_refund_reason(self, reason: str) -> str:
        """Mapeia razão do refund para Stripe"""
        mapping = {
            "user_requested": "requested_by_customer",
            "fraud_suspicion": "fraudulent"
        }
        return mapping.get(reason, "requested_by_customer")

    def get_payment_status(self, provider_payment_id: str) -> PaymentResult:
        # Implementação existente...
        pass