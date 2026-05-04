import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _inv_root() -> Path:
    return Path(__file__).resolve().parents[2] / "inventory_service"


def test_emit_wallet_event_paths():
    root = _inv_root()
    sys.path.insert(0, str(root))
    from infra.kafka import producers  # noqa: WPS433

    with patch.object(producers, "KafkaProducer", None):
        assert producers.emit_wallet_event("localhost:1", "wallet.credited", {"user_id": "u"}) is False


@patch("infra.kafka.producers.KafkaProducer")
def test_emit_notification_event(mock_kp):
    root = _inv_root()
    sys.path.insert(0, str(root))
    from infra.kafka import producers  # noqa: WPS433

    p = MagicMock()
    mock_kp.return_value = p
    assert producers.emit_notification_event("localhost:1", "queued", {"id": "1"}) is True
    p.send.assert_called()
    p.flush.assert_called()
    p.close.assert_called()
