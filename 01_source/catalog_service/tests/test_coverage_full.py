from __future__ import annotations

from unittest import mock

import httpx
import pytest

from app.core.database import SessionLocal, init_db
from app.events import publishers, replay, streams
from app.models.compatibility import Locker, PartnerProductRule
from app.models.dimensions import ProductDimensions
from app.models.product import Product
from app.services import catalog_service, compatibility_service, webhook_service

PID = "11111111-1111-1111-1111-111111111111"


def test_update_price_missing_raises():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        with pytest.raises(catalog_service.CatalogError):
            catalog_service.update_price(db, mock.MagicMock(), "00000000-0000-0000-0000-000000000001", 1)
    finally:
        db.close()


def test_deprecate_missing_raises():
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(catalog_service.CatalogError):
            catalog_service.deprecate_product(db, mock.MagicMock(), "00000000-0000-0000-0000-000000000001")
    finally:
        db.close()


def test_apply_price_empty_sku():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_PRICE_CHANGED, {"price_cents": 1})
    finally:
        db.close()


def test_apply_synced_non_dict_snapshot():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_SYNCED, {"snapshot": "bad"})
    finally:
        db.close()


def test_apply_synced_with_dict_snapshot():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        snap = {
            "sku_id": "abababab-abab-abab-abab-abababababab",
            "partner_id": PID,
            "partner_sku": "SYNCIN",
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
        }
        catalog_service.apply_stream_event(db, streams.PRODUCT_SYNCED, {"snapshot": snap})
        assert db.query(Product).filter(Product.sku_id == snap["sku_id"]).first()
    finally:
        db.close()


def test_create_product_generic_catalog_error(client, monkeypatch):
    def boom(*a, **k):
        raise catalog_service.CatalogError("other")

    monkeypatch.setattr(catalog_service, "ensure_category", boom)
    r = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "GE",
            "name": "g",
            "category_id": "GENERAL",
            "price_cents": 1,
            "dimensions": {"weight_g": 1},
        },
    )
    assert r.status_code == 400


def test_cache_get_json_bytes(monkeypatch, fake_redis):
    monkeypatch.setattr(fake_redis, "get", lambda k: b'{"x": 1}')
    from app.services import cache_service

    assert cache_service.get_json(fake_redis, "k") == {"x": 1}


def test_weight_exceeds_xl_slot():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="11111111-1111-1111-1111-111111111112",
            partner_id=PID,
            partner_sku="XLW",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        p.dimensions = ProductDimensions(id="dxl", product_sku_id=p.sku_id, weight_g=5000)
        db.add(p)
        db.add(Locker(id="Lxl", partner_id=PID, site_id="s", slot_size="XL", max_weight_g=1000))
        db.commit()
        lk = db.query(Locker).filter_by(id="Lxl").first()
        r = compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None)
        assert r.recommended_slot_size == "OVERSIZE"
    finally:
        db.close()


def test_engine_kwargs_postgres():
    from app.core.database import _engine_kwargs

    assert "pool_pre_ping" in _engine_kwargs("postgresql://localhost/db")


def test_replay_empty_stream(fake_redis):
    init_db()
    db = SessionLocal()
    try:
        assert replay.replay_range(fake_redis, db, handler=lambda *a: None, count=5) == 0
    finally:
        db.close()


def test_events_replay_http(client, fake_redis):
    pl = {
        "sku_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        "partner_id": PID,
        "partner_sku": "REPHTTP",
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
    }
    publishers.publish_product_created(fake_redis, pl)
    r = client.post("/api/v1/events/replay", json={"start_id": "0", "count": 20})
    assert r.status_code == 200
    assert r.json()["replayed"] >= 1


def test_bulk_partial_errors(client):
    r = client.post(
        "/api/v1/products/bulk",
        json={
            "partner_id": PID,
            "items": [
                {"partner_sku": "BOK", "name": "a", "category_id": "GENERAL", "price_cents": 1},
                {"partner_sku": "BOK", "name": "b", "category_id": "GENERAL", "price_cents": 2},
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["errors"]) >= 1


def test_get_product_bad_cache_shape(client, fake_redis):
    sku = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "BADSHAPE",
            "name": "x",
            "category_id": "GENERAL",
            "price_cents": 1,
            "dimensions": {"weight_g": 1},
        },
    ).json()["sku_id"]
    client.get(f"/api/v1/products/{sku}")
    from app.services import cache_service

    fake_redis.set(cache_service.cache_key_product(sku), '{"sku_id": "only"}')
    r = client.get(f"/api/v1/products/{sku}")
    assert r.status_code == 200


def test_create_emit_events_off():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        from app.schemas.product import ProductCreateIn

        r = catalog_service.create_product(
            db,
            mock.MagicMock(),
            PID,
            ProductCreateIn(
                partner_sku="NE",
                name="n",
                category_id="GENERAL",
                price_cents=1,
            ),
            emit_events=False,
        )
        assert r.sku_id
    finally:
        db.close()


def test_update_price_emit_off(fake_redis):
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
            partner_id=PID,
            partner_sku="UP",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        db.add(p)
        db.commit()
        catalog_service.update_price(db, fake_redis, p.sku_id, 99, emit_events=False)
    finally:
        db.close()


def test_deprecate_emit_off(fake_redis):
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="99999999-9999-9999-9999-999999999999",
            partner_id=PID,
            partner_sku="DEP",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        db.add(p)
        db.commit()
        catalog_service.deprecate_product(db, fake_redis, p.sku_id, emit_events=False)
    finally:
        db.close()


def test_apply_created_no_sku():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_CREATED, {"partner_id": PID})
    finally:
        db.close()


def test_apply_price_with_version():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
            partner_id=PID,
            partner_sku="PV",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        db.add(p)
        db.commit()
        catalog_service.apply_stream_event(
            db, streams.PRODUCT_PRICE_CHANGED, {"sku_id": p.sku_id, "price_cents": 50, "version": 9}
        )
        db.refresh(p)
        assert p.version == 9
    finally:
        db.close()


def test_apply_deprecated_with_product():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
            partner_id=PID,
            partner_sku="DP",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        db.add(p)
        db.commit()
        catalog_service.apply_stream_event(db, streams.PRODUCT_DEPRECATED, {"sku_id": p.sku_id})
        db.refresh(p)
        assert p.is_active is False
    finally:
        db.close()


def test_allowed_temp_not_list():
    P3 = "33333333-3333-3333-3333-333333333333"
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        db.add(PartnerProductRule(partner_id=P3, allowed_temperature_zones='"AMBIENT"'))
        p = Product(
            sku_id="cccccccc-cccc-cccc-cccc-ccccccccccc1",
            partner_id=P3,
            partner_sku="T1",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            temperature_zone="AMBIENT",
            version=1,
        )
        p.dimensions = ProductDimensions(id="d2", product_sku_id=p.sku_id, weight_g=1)
        db.add(p)
        lk = Locker(id="L2", partner_id=P3, site_id="s", slot_size="M", max_weight_g=5000)
        db.add(lk)
        db.commit()
        r = compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None)
        assert r.compatible is True
    finally:
        db.close()


def test_compat_weight_exceeds():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="dddddddd-dddd-dddd-dddd-ddddddddddd1",
            partner_id=PID,
            partner_sku="CX",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            temperature_zone="AMBIENT",
            version=1,
        )
        p.dimensions = ProductDimensions(id="d3", product_sku_id=p.sku_id, weight_g=100)
        db.add(p)
        db.add(Locker(id="Lheavy", partner_id=PID, site_id="s", slot_size="M", max_weight_g=10))
        db.commit()
        heavy = db.query(Locker).filter_by(id="Lheavy").first()
        assert not compatibility_service.is_product_compatible_with_locker(db, p, locker=heavy, locker_spec=None).compatible
    finally:
        db.close()


def test_compat_temperature_and_rule_and_hazard():
    P2 = "22222222-2222-2222-2222-222222222222"
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        db.add(
            PartnerProductRule(
                partner_id=P2,
                category_id="GENERAL",
                allowed_temperature_zones='["REFRIGERATED"]',
                max_weight_g=30,
                requires_signature=True,
                is_hazardous_allowed=False,
            )
        )
        p = Product(
            sku_id="dddddddd-dddd-dddd-dddd-ddddddddddd2",
            partner_id=P2,
            partner_sku="CX2",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            temperature_zone="AMBIENT",
            requires_signature=False,
            is_hazardous=True,
            version=1,
        )
        p.dimensions = ProductDimensions(id="d3b", product_sku_id=p.sku_id, weight_g=10)
        db.add(p)
        db.add(Locker(id="Lm", partner_id=P2, site_id="s", slot_size="M", max_weight_g=5000))
        db.commit()
        lk = db.query(Locker).filter_by(id="Lm").first()
        assert compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None).reason == "TEMPERATURE_NOT_ALLOWED"
        p.temperature_zone = "REFRIGERATED"
        p.requires_signature = True
        p.is_hazardous = False
        p.dimensions.weight_g = 50
        db.commit()
        assert compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None).reason == "RULE_WEIGHT_EXCEEDED"
        p.dimensions.weight_g = 10
        p.requires_signature = False
        db.commit()
        assert compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None).reason == "SIGNATURE_REQUIRED"
        p.requires_signature = True
        p.is_hazardous = True
        db.commit()
        assert compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None).reason == "HAZARDOUS_NOT_ALLOWED"
    finally:
        db.close()


def test_compat_slot_s():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="dddddddd-dddd-dddd-dddd-ddddddddddd3",
            partner_id=PID,
            partner_sku="CX3",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        p.dimensions = ProductDimensions(id="d3c", product_sku_id=p.sku_id, weight_g=3000)
        db.add(p)
        db.add(Locker(id="Ls", partner_id=PID, site_id="s", slot_size="S", max_weight_g=9000))
        db.commit()
        lk = db.query(Locker).filter_by(id="Ls").first()
        assert compatibility_service.is_product_compatible_with_locker(db, p, locker=lk, locker_spec=None).reason == "SLOT_TOO_SMALL"
    finally:
        db.close()


def test_webhook_get_bytes(monkeypatch, fake_redis):
    monkeypatch.setattr(fake_redis, "hget", lambda *a, **k: b'{"url":"http://x.test/h","events":["*"]}')
    assert webhook_service.get_webhook(fake_redis, "p1")["url"] == "http://x.test/h"


def test_deliver_sync_bad_status(monkeypatch):
    class MC:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 500
            r.is_success = False
            r.text = "err"
            return r

    monkeypatch.setattr(httpx, "Client", lambda **k: MC())
    code, err = webhook_service.deliver_sync("http://u", None, "t", {})
    assert code == 500
    assert err == "err"


def test_notify_empty_url(monkeypatch, fake_redis):
    monkeypatch.setattr(webhook_service, "get_webhook", lambda *a, **k: {"url": "", "events": ["*"]})
    webhook_service.notify_partner(fake_redis, "p", "product.created", {})


def test_compat_check_failed_messages_fallback(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        p = Product(
            sku_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1",
            partner_id=PID,
            partner_sku="FM",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            version=1,
        )
        p.dimensions = ProductDimensions(id="d4", product_sku_id=p.sku_id, weight_g=1)
        db.add(p)
        db.add(Locker(id="Ltiny", partner_id=PID, site_id="s", slot_size="M", max_weight_g=100))
        db.commit()

        def fake_compat(*a, **k):
            return compatibility_service.CompatibilityResult(False, reason=None, failed_messages=["z"])

        monkeypatch.setattr(compatibility_service, "is_product_compatible_with_locker", fake_compat)
        from app.routers.compatibility import check_by_partner_sku
        from app.schemas.compatibility import ProductCompatibilityCheckIn

        r = check_by_partner_sku(PID, ProductCompatibilityCheckIn(partner_sku="FM", locker_id="Ltiny"), db)
        assert r.reason == "z"
    finally:
        db.close()
