# 01_source/payment_gateway/app/integrations/payments/mercadopago/client.py

import httpx
from datetime import datetime
from app.integrations.payments.base.contracts import (
    CreatePaymentCommand,
    PaymentResult,
    CancelPaymentCommand,
    CancelPaymentResult
)
from app.integrations.payments.base.exceptions import PaymentProviderError


class MercadoPagoClient:
    provider_name = "mercadopago"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.base_url = "https://api.mercadopago.com/v1"

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        # Implementação existente...
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"mp_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
    
    async def cancel_payment(self, command: CancelPaymentCommand) -> CancelPaymentResult:
        """
        Implementa cancelamento/refund no MercadoPago.
        
        Para MP:
        - Pagamentos pendentes: Cancelamento via DELETE
        - Pagamentos aprovados: Refund via POST /payments/{id}/refunds
        """
        try:
            async with httpx.AsyncClient() as client:
                # Primeiro, verificar status do pagamento
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # GET para obter status atual
                status_response = await client.get(
                    f"{self.base_url}/payments/{command.provider_payment_id}",
                    headers=headers
                )
                
                if status_response.status_code == 404:
                    return CancelPaymentResult(
                        success=False,
                        provider=self.provider_name,
                        refund_id="",
                        status="FAILED",
                        error=f"Payment {command.provider_payment_id} not found"
                    )
                
                status_response.raise_for_status()
                payment_data = status_response.json()
                payment_status = payment_data.get("status")
                
                # Decidir ação baseada no status
                if payment_status == "pending":
                    # Cancelar pagamento pendente
                    cancel_response = await client.delete(
                        f"{self.base_url}/payments/{command.provider_payment_id}",
                        headers=headers
                    )
                    cancel_response.raise_for_status()
                    
                    return CancelPaymentResult(
                        success=True,
                        provider=self.provider_name,
                        refund_id=command.provider_payment_id,
                        status="CANCELLED",
                        processed_at=datetime.utcnow()
                    )
                    
                elif payment_status == "approved":
                    # Fazer refund para pagamento aprovado
                    refund_data = {
                        "payment_id": command.provider_payment_id,
                        "reason": command.reason
                    }
                    
                    if command.amount:
                        refund_data["amount"] = command.amount
                    
                    refund_response = await client.post(
                        f"{self.base_url}/payments/{command.provider_payment_id}/refunds",
                        headers=headers,
                        json=refund_data
                    )
                    refund_response.raise_for_status()
                    
                    refund_data_response = refund_response.json()
                    
                    return CancelPaymentResult(
                        success=True,
                        provider=self.provider_name,
                        refund_id=refund_data_response.get("id", command.provider_payment_id),
                        status="REFUNDED",
                        processed_at=datetime.utcnow()
                    )
                    
                else:
                    return CancelPaymentResult(
                        success=False,
                        provider=self.provider_name,
                        refund_id="",
                        status="FAILED",
                        error=f"Cannot cancel payment with status: {payment_status}"
                    )
                    
        except httpx.HTTPStatusError as e:
            return CancelPaymentResult(
                success=False,
                provider=self.provider_name,
                refund_id="",
                status="FAILED",
                error=f"MercadoPago API error: {str(e)}"
            )
        except Exception as e:
            return CancelPaymentResult(
                success=False,
                provider=self.provider_name,
                refund_id="",
                status="FAILED",
                error=f"Unexpected error: {str(e)}"
            )

    def get_payment_status(self, provider_payment_id: str) -> PaymentResult:
        # Implementação existente...
        pass

    