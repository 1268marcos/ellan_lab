from app.events import stream_keys
from app.events.publisher import publish_event
from app.services import double_write


def test_stream_keys():
    assert stream_keys.PAYMENT_CONFIRMED.startswith("payment.")


def test_double_write_no_redis():
    assert double_write.mirror_inventory_state(None, "s", 1, 1) is None
    assert double_write.replay_mirror_count(None) == 0


def test_double_write_with_redis(client):
    r = client.app.state.redis
    assert double_write.mirror_inventory_state(r, "s2", 4, 2) is not None
    assert double_write.replay_mirror_count(r) >= 1


def test_register_avro_schema_shape():
    from infra.kafka import schema_registry

    s = schema_registry.inventory_movement_avro_schema()
    assert s["type"] == "record"


def test_publish_event_none():
    assert publish_event(None, "x", {}) is None
