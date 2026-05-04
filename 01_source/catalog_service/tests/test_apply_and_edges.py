from __future__ import annotations

import json

from app.core.database import SessionLocal, init_db
from app.events import streams
from app.models.product import Product
from app.services import catalog_service

PID = "11111111-1111-1111-1111-111111111111"


def test_apply_price_changed_missing_product():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_PRICE_CHANGED, {"sku_id": "00000000-0000-0000-0000-000000000099", "price_cents": 9})
    finally:
        db.close()


def test_apply_deprecated_missing_sku():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_DEPRECATED, {})
    finally:
        db.close()


def test_apply_synced_no_snapshot():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.apply_stream_event(db, streams.PRODUCT_SYNCED, {})
    finally:
        db.close()


def test_apply_created_idempotent():
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        snap = {
            "sku_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "partner_id": PID,
            "partner_sku": "IDEM",
            "name": "i",
            "description": None,
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
        catalog_service.apply_stream_event(db, streams.PRODUCT_CREATED, snap)
        catalog_service.apply_stream_event(db, streams.PRODUCT_CREATED, snap)
        assert db.query(Product).filter_by(sku_id=snap["sku_id"]).count() == 1
    finally:
        db.close()


def test_assert_partner_active_error():
    try:
        catalog_service.assert_partner_active("short")
        assert False
    except catalog_service.CatalogError:
        pass


def test_replay_payload_bad_json(fake_redis):
    fake_redis.xadd("catalog:events", {"event_type": "x", "payload": "not-json", "occurred_at": "t"})
    init_db()
    db = SessionLocal()
    try:
        from app.events import replay

        n = replay.replay_range(fake_redis, db, handler=lambda *a: None, count=5)
        assert n == 0
    finally:
        db.close()


def test_compatibility_rule_json_bad():
    from app.models.compatibility import PartnerProductRule
    from app.models.product import Product
    from app.models.dimensions import ProductDimensions
    from app.services import compatibility_service

    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        db.add(PartnerProductRule(partner_id=PID, category_id=None, allowed_temperature_zones="not-json"))
        p = Product(
            sku_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            partner_id=PID,
            partner_sku="R1",
            name="n",
            category_id="GENERAL",
            price_cents=1,
            currency="BRL",
            images="[]",
            temperature_zone="AMBIENT",
            version=1,
        )
        p.dimensions = ProductDimensions(id="d1", product_sku_id=p.sku_id, weight_g=1)
        db.add(p)
        db.commit()
        locker = __import__("app.models.compatibility", fromlist=["Locker"]).Locker(
            id="L1", partner_id=PID, site_id="s", slot_size="M", max_weight_g=9000
        )
        db.add(locker)
        db.commit()
        r = compatibility_service.is_product_compatible_with_locker(db, p, locker=locker, locker_spec=None)
        assert r.compatible is True
    finally:
        db.close()


def test_versioning_header():
    from app.core import versioning

    assert versioning.dto_version_header_value() == "v1"
