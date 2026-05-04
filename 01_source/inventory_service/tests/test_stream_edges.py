import json

import fakeredis

from app.core.config import get_settings
from app.services import double_write
from app.services.idempotency import IdempotencyStore
from app.workers import stream_consumer


def test_consume_once_skips_bad_payload(client):
    r = client.app.state.redis
    settings = get_settings()
    r.xadd(settings.events_stream, {"data": "not-json"})
    assert stream_consumer.consume_once(r, store=IdempotencyStore(None)) == 0


def test_push_dlq_roundtrip():
    r = fakeredis.FakeRedis(decode_responses=False)
    settings = get_settings()
    stream_consumer.push_dlq(r, "1-0", {"data": b"x"}, "err")
    entries = r.xrevrange(settings.dlq_stream, count=1)
    assert entries


def test_parse_empty_data_string():
    assert stream_consumer._parse({"data": ""}) is None


def test_parse_bytes_fields():
    raw = {b"data": json.dumps({"type": "payment.confirmed", "payload": {"order_id": "o"}}).encode()}
    obj = stream_consumer._parse(raw)
    assert obj is not None
    assert obj["type"] == "payment.confirmed"


def test_push_dlq_no_redis():
    stream_consumer.push_dlq(None, "1", {"data": "x"}, "e")


def test_double_write_replay_error():
    class R:
        def xlen(self, _k):
            raise RuntimeError("boom")

    assert double_write.replay_mirror_count(R()) == 0  # type: ignore[arg-type]
