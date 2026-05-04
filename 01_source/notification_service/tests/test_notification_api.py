from app.services import email, queue_consumer, sms, whatsapp


def test_health(client):
    assert client.get("/api/v1/health").json()["service"] == "notification-service"


def test_queue_and_status(client):
    r = client.post("/api/v1/queue", json={"channel": "email", "payload": "hello {{order_id}}", "order_id": "o1"})
    nid = r.json()["id"]
    s = client.get(f"/api/v1/status/{nid}")
    assert s.json()["status"] == "queued"


def test_status_not_found(client):
    assert client.get("/api/v1/status/00000000-0000-0000-0000-000000000099").status_code == 404


def test_template_create(client):
    r = client.post("/api/v1/templates", json={"name": "t1", "body": "x {{order_id}} y"})
    assert r.status_code == 201


def test_queue_enqueue_redis(client):
    r = client.app.state.redis
    assert queue_consumer.enqueue(r, "k", {"a": 1}) is not None


def test_queue_enqueue_none():
    assert queue_consumer.enqueue(None, "k", {"a": 1}) is None


def test_queue_dequeue_none():
    assert queue_consumer.dequeue(None, "k") is None


def test_queue_roundtrip(client):
    r = client.app.state.redis
    queue_consumer.enqueue(r, "q1", {"z": 2})
    assert queue_consumer.dequeue(r, "q1") == {"z": 2}


def test_email_render():
    assert "o" in email.render_email("{{order_id}}", "o")


def test_sms_render():
    assert sms.render_sms("{{order_id}}", "1") == "1"


def test_whatsapp_render():
    assert "a" in whatsapp.render_whatsapp("a{{order_id}}b", "z")


def test_sms_send_empty():
    assert sms.send_sms("+1", "") is False


def test_whatsapp_send_empty():
    assert whatsapp.send_whatsapp("+1", "") is False


def test_dequeue_rpop_none():
    class R:
        def rpop(self, _k):
            return None

    assert queue_consumer.dequeue(R(), "k") is None  # type: ignore[arg-type]


def test_queue_consumer_bytes_payload():
    r = __import__("fakeredis").FakeRedis(decode_responses=False)
    from app.services import queue_consumer

    queue_consumer.enqueue(r, "qb", {"a": 1})
    out = queue_consumer.dequeue(r, "qb")
    assert out == {"a": 1}


def test_dlq_push_none():
    from app.workers import delivery_worker

    delivery_worker.push_dlq(None, {"id": "x"})


def test_dlq_push(client):
    from app.workers import delivery_worker

    delivery_worker.push_dlq(client.app.state.redis, {"id": "d"})
    raw = client.app.state.redis.lpop("notification:dlq")
    assert raw


def test_rate_limited_false_without_redis():
    from app.workers import delivery_worker

    assert delivery_worker.rate_limited(None, "k") is False


def test_queue_invalid_channel(client):
    assert client.post("/api/v1/queue", json={"channel": "fax", "payload": "x"}).status_code == 422


def test_template_unique_name(client):
    client.post("/api/v1/templates", json={"name": "uniq", "body": "b"})
    assert client.post("/api/v1/templates", json={"name": "uniq", "body": "c"}).status_code == 409
