"""Contrato HTTP pickup → order_lifecycle (cancelar deadline de pré-pagamento)."""
from unittest.mock import MagicMock, patch

from app.core.lifecycle_client import LifecycleClient


def test_cancel_prepayment_deadline_posts_expected_body():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"ok":true}'
    mock_resp.json.return_value = {"ok": True}

    with patch("app.core.lifecycle_client.requests.request", return_value=mock_resp) as req:
        client = LifecycleClient(
            base_url="http://lifecycle.test",
            timeout_sec=2.0,
            internal_token="secret-token",
        )
        out = client.cancel_prepayment_deadline(order_id="ord-123")

    req.assert_called_once()
    kwargs = req.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "http://lifecycle.test/internal/deadlines/cancel"
    assert kwargs["json"] == {"deadline_key": "order:ord-123:prepayment_timeout"}
    assert kwargs["headers"]["X-Internal-Token"] == "secret-token"
    assert out == {"ok": True}
