from unittest.mock import MagicMock, patch

from infra.kafka import consumers, producers, schema_registry


@patch("infra.kafka.admin.KafkaAdminClient", side_effect=RuntimeError("ctor"))
def test_admin_ctor_fails(_mock):
    from infra.kafka import admin as kafka_admin

    names = kafka_admin.ensure_topics("localhost:1")
    assert "catalog-stream" in names


@patch("infra.kafka.producers.KafkaProducer")
def test_emit_product_flush_fails(mock_kp):
    p = MagicMock()
    p.send.return_value = None
    p.flush.side_effect = RuntimeError("flush")
    mock_kp.return_value = p
    assert producers.emit_product_event("localhost:1", "product.updated", {"sku": "1"}) is False


@patch("infra.kafka.producers.KafkaProducer")
def test_emit_wallet_and_notification_streams(mock_kp):
    p = MagicMock()
    mock_kp.return_value = p
    assert producers.emit_wallet_event("localhost:1", "wallet.credited", {"user_id": "u"}) is True
    assert producers.emit_notification_event("localhost:1", "queued", {"id": "1"}) is True


@patch("infra.kafka.producers.KafkaProducer")
def test_emit_close_fails(mock_kp):
    p = MagicMock()
    p.send.return_value = None
    p.flush.return_value = None
    p.close.side_effect = RuntimeError("close")
    mock_kp.return_value = p
    assert producers.emit_order_event("localhost:1", "order.expired", {"order_id": "1"}) is False


@patch("infra.kafka.producers.KafkaProducer", side_effect=RuntimeError("ctor"))
def test_producer_ctor_raises(_mock):
    assert producers.emit_product_event("localhost:1", "product.updated", {"sku": "1"}) is False


def test_kafka_producer_none_class(monkeypatch):
    import infra.kafka.producers as pr

    monkeypatch.setattr(pr, "KafkaProducer", None)
    assert pr.emit_product_event("localhost:1", "product.updated", {"sku": "1"}) is False


def test_admin_kafka_import_none_branch(monkeypatch):
    import infra.kafka.admin as ka

    monkeypatch.setattr(ka, "KafkaAdminClient", None)
    monkeypatch.setattr(ka, "NewTopic", None)
    assert "catalog-stream" in ka.ensure_topics("localhost:1")


def test_kafka_consumer_module_none():
    with patch("infra.kafka.consumers.KafkaConsumer", None):
        assert consumers.inventory_consumer("localhost:1", ("order-stream",), "g", lambda m: None) is None


@patch("infra.kafka.consumers.KafkaConsumer", side_effect=RuntimeError("no"))
def test_inventory_consumer_constructor_fails(_mock):
    assert consumers.inventory_consumer("localhost:1", ("order-stream",), "g", lambda m: None) is None


@patch("infra.kafka.producers.KafkaProducer", side_effect=RuntimeError("no"))
def test_producer_constructor_fails(_mock):
    assert producers.emit_order_event("localhost:1", "order.expired", {"order_id": "1"}) is False


def test_poll_batch_poll_raises():
    c = MagicMock()
    c.poll.side_effect = RuntimeError("x")
    assert consumers.poll_batch(c) == []


@patch("infra.kafka.admin.KafkaAdminClient")
def test_admin_close_raises(mock_cls):
    from infra.kafka import admin as kafka_admin

    inst = MagicMock()
    inst.list_topics.return_value = ["catalog-stream", "payment-stream", "order-stream"]
    inst.close.side_effect = RuntimeError("close")
    mock_cls.return_value = inst
    assert "catalog-stream" in kafka_admin.ensure_topics("localhost:1")


@patch("infra.kafka.admin.KafkaAdminClient")
def test_admin_create_topics_raises(mock_cls):
    from infra.kafka import admin as kafka_admin

    inst = MagicMock()
    inst.list_topics.return_value = []
    inst.create_topics.side_effect = RuntimeError("nope")
    mock_cls.return_value = inst
    names = kafka_admin.ensure_topics("localhost:1")
    assert "catalog-stream" in names


def test_schema_registry_ok():
    class Resp:
        def read(self):
            return b'{"id": 7}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("infra.kafka.schema_registry.urllib.request.urlopen", return_value=Resp()):
        rid = schema_registry.register_avro_schema("http://reg", "subj", {"type": "record", "name": "A", "fields": []})
        assert rid == 7
