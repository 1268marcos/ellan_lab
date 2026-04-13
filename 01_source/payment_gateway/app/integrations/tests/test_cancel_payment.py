# 01_source/payment_gateway/app/integrations/tests/test_cancel_payment.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)


def test_cancel_payment_success():
    """Testa cancelamento bem sucedido"""
    mock_event = Mock()
    mock_event.decision = "APPROVED"
    mock_event.provider = "stripe"
    mock_event.region = "SP"
    mock_event.provider_payment_id = "pi_123"
    
    mock_result = Mock()
    mock_result.success = True
    mock_result.refund_id = "re_123"
    mock_result.status = "REFUNDED"
    mock_result.processed_at = datetime.utcnow()
    
    with patch('app.routers.payment.RiskEventsService.get_event_by_order_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_event
        
        with patch('app.routers.payment.build_stripe_sp') as mock_provider:
            mock_provider.return_value.cancel_payment = AsyncMock(return_value=mock_result)
            
            response = client.post(
                "/gateway/pagamento/ORD123/cancel",
                headers={"Idempotency-Key": "test-key-123"},
                json={
                    "reason": "user_requested",
                    "requested_by": "customer"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["cancelled"] is True
            assert data["provider_refund_id"] == "re_123"


def test_cancel_payment_not_found():
    """Testa pagamento não encontrado"""
    with patch('app.routers.payment.RiskEventsService.get_event_by_order_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = client.post(
            "/gateway/pagamento/INVALID/cancel",
            headers={"Idempotency-Key": "test-key-123"},
            json={
                "reason": "user_requested",
                "requested_by": "customer"
            }
        )
        
        assert response.status_code == 404
        assert "Payment not found" in response.json()["detail"]


def test_cancel_payment_wrong_status():
    """Testa cancelamento com status inválido"""
    mock_event = Mock()
    mock_event.decision = "PENDING"  # Não pode cancelar
    
    with patch('app.routers.payment.RiskEventsService.get_event_by_order_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_event
        
        response = client.post(
            "/gateway/pagamento/ORD123/cancel",
            headers={"Idempotency-Key": "test-key-123"},
            json={
                "reason": "user_requested",
                "requested_by": "customer"
            }
        )
        
        assert response.status_code == 422
        assert "cannot be cancelled" in response.json()["detail"]

