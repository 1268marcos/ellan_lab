from unittest.mock import MagicMock, patch

from infra.kafka import admin, consumers, producers, schema_registry, serializers, topics


def test_topics_constants():
    assert topics.CATALOG_STREAM == "catalog-stream"


def test_serializers_roundtrip():
    b = serializers.json_dumps({"a": 1})
    assert serializers.json_loads(b) == {"a": 1}


def test_schema_registry_offline():
    assert schema_registry.register_avro_schema("http://127.0.0.1:9", "sub", {"type": "record", "name": "X", "fields": []}) == 0


def test_producers_without_kafka():
    assert producers.emit_product_event("localhost:1", "product.updated", {"sku": "1"}) is False


def test_admin_without_kafka():
    names = admin.ensure_topics("localhost:1")
    assert "catalog-stream" in names


@patch("infra.kafka.admin.KafkaAdminClient")
def test_admin_with_kafka(mock_cls):
    inst = MagicMock()
    inst.list_topics.return_value = []
    mock_cls.return_value = inst
    admin.ensure_topics("localhost:1")
    inst.close.assert_called()


@patch("infra.kafka.producers.KafkaProducer")
def test_producer_send(mock_kp):
    p = MagicMock()
    mock_kp.return_value = p
    assert producers.emit_payment_event("localhost:1", "payment.confirmed", {"order_id": "a"}) is True
    p.send.assert_called()
    p.flush.assert_called()
    p.close.assert_called()


@patch("infra.kafka.consumers.KafkaConsumer")
def test_consumer_poll(mock_kc):
    rec = MagicMock()
    rec.value = {"type": "x"}
    tp = MagicMock()
    mock_inst = MagicMock()
    mock_inst.poll.return_value = {tp: [rec]}
    mock_kc.return_value = mock_inst
    c = consumers.inventory_consumer("localhost:1", ("order-stream",), "g", lambda m: None)
    batch = consumers.poll_batch(c)
    assert batch == [{"type": "x"}]


def test_poll_batch_none():
    assert consumers.poll_batch(None) == []
