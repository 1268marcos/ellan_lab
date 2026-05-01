"""Contrato HTTP gateway → backend_runtime (set-state após pagamento)."""
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.locker_backend_client import LockerBackendClient


def test_set_state_posts_paid_pending_pickup_payload():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ok": True, "slot": 3, "state": "PAID_PENDING_PICKUP"}
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.locker_backend_client.requests.post", return_value=mock_resp) as post:
        client = LockerBackendClient("http://runtime.test", timeout_sec=3)
        out = client.set_state(
            porta=3,
            state="PAID_PENDING_PICKUP",
            locker_id="SP-TEST-LOCKER-001",
        )

    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "http://runtime.test/locker/slots/3/set-state"
    assert kwargs["json"] == {"state": "PAID_PENDING_PICKUP", "product_id": None}
    assert kwargs["headers"] == {"X-Locker-Id": "SP-TEST-LOCKER-001"}
    assert kwargs["timeout"] == 3
    assert out == {"ok": True, "slot": 3, "state": "PAID_PENDING_PICKUP"}


def test_set_state_propagates_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("502")

    with patch("app.services.locker_backend_client.requests.post", return_value=mock_resp):
        client = LockerBackendClient("http://runtime.test", timeout_sec=1)
        with pytest.raises(requests.HTTPError, match="502"):
            client.set_state(porta=1, state="PAID_PENDING_PICKUP", locker_id="LK-1")
