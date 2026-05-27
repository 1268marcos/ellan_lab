# 01_source/payment_gateway/app/integrations/tests/test_payment_cancellation.py


import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.payments.base.contracts import CancelPaymentCommand
from app.integrations.payments.mercadopago.client import MercadoPagoClient
from app.integrations.payments.stripe.client import StripeClient
from app.integrations.payments.base.exceptions import PaymentValidationError


class TestMercadoPagoCancellation:
    
    def test_cancel_pending_payment(self, mp_client):
        """Testa cancelamento de pagamento pendente no MercadoPago"""
        command = CancelPaymentCommand(
            provider_payment_id="mp_123456",
            reason="user_requested"
        )
        
        with patch.object(mp_client.session, 'delete') as mock_delete:
            mock_delete.return_value.status_code = 200
            mock_delete.return_value.json.return_value = {"status": "cancelled"}
            
            with patch.object(mp_client, '_get_payment_status_from_api') as mock_status:
                mock_status.return_value = {"status": "pending"}
                
                result = mp_client.cancel_payment(command)
                
                assert result.status == "CANCELLED"
                assert result.provider_payment_id == "mp_123456"
    
    def test_refund_approved_payment(self, mp_client):
        """Testa reembolso de pagamento aprovado no MercadoPago"""
        command = CancelPaymentCommand(
            provider_payment_id="mp_123456",
            reason="user_requested",
            amount=100.00
        )
        
        with patch.object(mp_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "refunded"}
            
            with patch.object(mp_client, '_get_payment_status_from_api') as mock_status:
                mock_status.return_value = {"status": "approved"}
                
                result = mp_client.cancel_payment(command)
                
                assert result.status == "REFUNDED"
    
    @pytest.fixture
    def mp_client(self):
        return MercadoPagoClient(access_token="test_token")


class TestStripeCancellation:

    @pytest.mark.asyncio
    async def test_cancel_uncaptured_payment(self):
        """Testa cancelamento de PaymentIntent não capturado"""
        payment_intent = Mock()
        payment_intent.status = "requires_capture"
        cancelled_intent = Mock()
        cancelled_intent.id = "pi_123"
        cancelled_intent.status = "canceled"

        with (
            patch(
                "app.integrations.payments.stripe.client.stripe.PaymentIntent.retrieve_async",
                new_callable=AsyncMock,
                return_value=payment_intent,
            ),
            patch(
                "app.integrations.payments.stripe.client.stripe.PaymentIntent.cancel_async",
                new_callable=AsyncMock,
                return_value=cancelled_intent,
            ) as mock_cancel,
        ):
            client = StripeClient(secret_key="test_key", account_region="US")
            command = CancelPaymentCommand(
                provider_payment_id="pi_123",
                reason="user_requested",
            )

            result = await client.cancel_payment(command)

            assert result.status == "CANCELLED"
            mock_cancel.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refund_succeeded_payment(self):
        """Testa refund de pagamento já capturado"""
        payment_intent = Mock()
        payment_intent.status = "succeeded"

        refund_mock = Mock()
        refund_mock.id = "re_123"
        refund_mock.status = "succeeded"
        refund_mock.created = 1_700_000_000
        refund_mock.payment_intent = "pi_123"

        with (
            patch(
                "app.integrations.payments.stripe.client.stripe.PaymentIntent.retrieve_async",
                new_callable=AsyncMock,
                return_value=payment_intent,
            ),
            patch(
                "app.integrations.payments.stripe.client.stripe.Refund.create_async",
                new_callable=AsyncMock,
                return_value=refund_mock,
            ) as mock_refund,
        ):
            client = StripeClient(secret_key="test_key", account_region="US")
            command = CancelPaymentCommand(
                provider_payment_id="pi_123",
                reason="user_requested",
            )

            result = await client.cancel_payment(command)

            assert result.status == "REFUNDED"
            mock_refund.assert_awaited_once()
