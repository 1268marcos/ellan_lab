import json

import fakeredis

from app.services.idempotency import IdempotencyStore


def test_idempotency_redis_roundtrip():
    r = fakeredis.FakeRedis(decode_responses=True)
    s = IdempotencyStore(r)
    s.set("k", {"a": 1})
    assert s.get("k") == {"a": 1}


def test_idempotency_redis_bytes():
    r = fakeredis.FakeRedis(decode_responses=False)
    r.set("idem:inventory:k2", json.dumps({"b": 2}))
    s = IdempotencyStore(r)
    assert s.get("k2") == {"b": 2}
