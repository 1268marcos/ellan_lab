"""Garante que o fluxo de confirmação de pagamento aciona cancelamento de deadline (lifecycle)."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers import internal as internal_router


def _minimal_order():
    order = MagicMock()
    order.id = "order-prepay-chain-1"
    order.region = "PT"
    order.channel = MagicMock()
    order.channel.value = "ONLINE"
    order.payment_method = MagicMock()
    order.payment_method.value = "CARD"
    order.totem_id = "LK-001"
    return order


def test_cancel_prepayment_wrapper_raises_http_exception_on_lifecycle_failure():
    order = _minimal_order()
    with patch(
        "app.routers.internal.cancel_prepayment_timeout_deadline",
        side_effect=RuntimeError("lifecycle down"),
    ):
        with pytest.raises(HTTPException) as ei:
            internal_router._cancel_prepayment_timeout_for_order(order)
        assert ei.value.status_code == 500


def test_cancel_prepayment_wrapper_calls_service_with_reason_metadata():
    order = _minimal_order()
    with patch("app.routers.internal.cancel_prepayment_timeout_deadline") as m:
        internal_router._cancel_prepayment_timeout_for_order(order)
    m.assert_called_once()
    _, kwargs = m.call_args
    assert kwargs["order_id"] == order.id
    assert kwargs["reason"] == "payment_confirmed"
    assert kwargs["metadata"]["source_service"] == "order_pickup_service"
    assert kwargs["metadata"]["order_id"] == order.id
