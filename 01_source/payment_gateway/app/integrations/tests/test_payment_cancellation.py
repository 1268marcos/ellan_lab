# 01_source/payment_gateway/app/integrations/tests/test_payment_cancellation.py


import pytest
from unittest.mock import Mock, patch
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
    
    def test_cancel_uncaptured_payment(self):
        """Testa cancelamento de PaymentIntent não capturado"""
        stripe_mock = Mock()
        stripe_mock.PaymentIntent.retrieve.return_value.status = "requires_capture"
        stripe_mock.PaymentIntent.cancel.return_value.id = "pi_123"
        stripe_mock.PaymentIntent.cancel.return_value.status = "canceled"
        
        with patch('stripe.PaymentIntent', stripe_mock.PaymentIntent):
            client = StripeClient(secret_key="test_key", account_region="US")
            command = CancelPaymentCommand(
                provider_payment_id="pi_123",
                reason="user_requested"
            )
            
            result = client.cancel_payment(command)
            
            assert result.status == "CANCELLED"
            stripe_mock.PaymentIntent.cancel.assert_called_once()
    
    def test_refund_succeeded_payment(self):
        """Testa refund de pagamento já capturado"""
        stripe_mock = Mock()
        payment_intent = Mock()
        payment_intent.status = "succeeded"
        stripe_mock.PaymentIntent.retrieve.return_value = payment_intent
        
        refund_mock = Mock()
        refund_mock.status = "succeeded"
        refund_mock.payment_intent = "pi_123"
        stripe_mock.Refund.create.return_value = refund_mock
        
        with patch('stripe.PaymentIntent', stripe_mock.PaymentIntent):
            with patch('stripe.Refund', stripe_mock.Refund):
                client = StripeClient(secret_key="test_key", account_region="US")
                command = CancelPaymentCommand(
                    provider_payment_id="pi_123",
                    reason="user_requested"
                )
                
                result = client.cancel_payment(command)
                
                assert result.status == "REFUNDED"
                stripe_mock.Refund.create.assert_called_once()
