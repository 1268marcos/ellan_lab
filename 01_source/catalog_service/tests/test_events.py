from __future__ import annotations

from app.core.database import SessionLocal, init_db
from app.events import publishers, replay, streams
from app.services import catalog_service

PID = "11111111-1111-1111-1111-111111111111"


def test_product_created_event(client):
    r = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "E1",
            "name": "E",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 1},
            "price_cents": 1,
        },
    )
    assert r.status_code == 201
    rid = client.app.state.redis_sync.xrevrange("catalog:events", count=5)
    assert len(rid) >= 1


def test_price_changed_event(client, fake_redis):
    sku = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "E2",
            "name": "E",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 1},
            "price_cents": 1,
        },
    ).json()["sku_id"]
    init_db()
    db = SessionLocal()
    try:
        catalog_service.update_price(db, fake_redis, sku, 999)
    finally:
        db.close()
    entries = fake_redis.xrevrange("catalog:events", count=20)
    found = False
    for _id, fields in entries:
        ft = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in fields.items()}
        if ft.get("event_type") == streams.PRODUCT_PRICE_CHANGED:
            found = True
            break
    assert found


def test_deprecated_event(client, fake_redis):
    sku = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "E3",
            "name": "E",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 1},
            "price_cents": 1,
        },
    ).json()["sku_id"]
    init_db()
    db = SessionLocal()
    try:
        catalog_service.deprecate_product(db, fake_redis, sku)
    finally:
        db.close()
    entries = fake_redis.xrevrange("catalog:events", count=20)
    found = any(
        (v.decode() if isinstance(v, bytes) else v) == streams.PRODUCT_DEPRECATED
        for _i, fld in entries
        for k, v in fld.items()
        if (k.decode() if isinstance(k, bytes) else k) == "event_type"
    )
    assert found


def test_event_replay(client, fake_redis):
    pl = {
        "sku_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "partner_id": PID,
        "partner_sku": "REP",
        "name": "R",
        "description": None,
        "category_id": "GENERAL",
        "price_cents": 5,
        "currency": "BRL",
        "images": [],
        "requires_signature": False,
        "is_hazardous": False,
        "temperature_zone": "AMBIENT",
        "version": 1,
        "is_active": True,
        "dimensions": {"width_mm": 1, "height_mm": 1, "depth_mm": 1, "weight_g": 1},
    }
    publishers.publish_product_created(fake_redis, pl)
    init_db()
    db = SessionLocal()
    try:
        n = replay.replay_range(
            fake_redis,
            db,
            handler=lambda s, et, p: catalog_service.apply_stream_event(s, et, p),
            start_id="0",
            count=50,
        )
        assert n >= 1
        from app.models.product import Product as P

        assert db.query(P).filter(P.sku_id == pl["sku_id"]).first()
    finally:
        db.close()


def test_publishers_wrappers(fake_redis):
    publishers.publish_price_changed(fake_redis, {"sku_id": "x", "price_cents": 1})
    publishers.publish_deprecated(fake_redis, {"sku_id": "x"})
    publishers.publish_synced(
        fake_redis,
        {
            "sku_id": "x",
            "snapshot": {
                "sku_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "partner_id": PID,
                "partner_sku": "SYNC",
                "name": "n",
                "category_id": "GENERAL",
                "price_cents": 1,
                "currency": "BRL",
                "images": [],
                "requires_signature": False,
                "is_hazardous": False,
                "temperature_zone": "AMBIENT",
                "version": 1,
                "is_active": True,
                "dimensions": {"weight_g": 1},
            },
        },
    )


def test_replay_xrange_error(monkeypatch, fake_redis):
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(fake_redis, "xrange", boom)
    init_db()
    db = SessionLocal()
    try:
        assert replay.replay_range(fake_redis, db, handler=lambda *a: None, count=1) == 0
    finally:
        db.close()
