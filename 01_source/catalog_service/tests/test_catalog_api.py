import json
import uuid
from unittest import mock

from config import settings
from database import SessionLocal
from events import publishers
from models import PartnerProductRule, Product


def _body(**kw):
    base = {
        "partner_sku": "SKU1",
        "name": "Item",
        "description": "d",
        "category_id": "CAT",
        "dimensions": {"width_mm": 10, "height_mm": 20, "depth_mm": 30, "weight_g": 40},
        "price_cents": 1000,
        "currency": "BRL",
        "images": [],
        "compatibility_rules": {
            "requires_signature": False,
            "is_fragile": False,
            "temperature_zone": "AMBIENT",
            "is_hazardous": False,
        },
    }
    base.update(kw)
    return base


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_categories(client):
    r = client.get("/api/v1/categories")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    ids = {x["id"] for x in data}
    assert ids == {"CAT", "ELECTRONICS_ACCESSORIES"}


def test_create_and_get_product(client, redis_client):
    r = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="A1"))
    assert r.status_code == 201
    sku = r.json()["sku_id"]
    g = client.get(f"/api/v1/products/{sku}")
    assert g.status_code == 200
    body = g.json()
    assert body["order_pickup_cache"]["sku_id"] == sku
    assert body["order_pickup_cache"]["partner_id"] == "p1"
    assert body["dimensions"]["width_mm"] == 10
    msgs = redis_client.xrange(settings.catalog_stream_key)
    assert len(msgs) >= 1
    assert json.loads(msgs[-1][1]["payload"])["sku_id"] == sku


def test_get_product_not_found(client):
    assert client.get(f"/api/v1/products/{uuid.uuid4()}").status_code == 404


def test_create_category_not_found(client):
    r = client.post(
        "/api/v1/partners/p1/products",
        json=_body(category_id="NOCAT"),
    )
    assert r.status_code == 404


def test_create_partner_inactive(client):
    r = client.post("/api/v1/partners/x-inactive/products", json=_body())
    assert r.status_code == 403


def test_check_compatibility_ok(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body()).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 100,
            "slot_height_mm": 100,
            "slot_depth_mm": 100,
            "max_weight_g": 500,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["compatible"] is True


def test_check_compatibility_not_registered(client):
    r = client.post(
        f"/api/v1/products/{uuid.uuid4()}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 100,
            "slot_height_mm": 100,
            "slot_depth_mm": 100,
            "max_weight_g": 500,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json() == {
        "compatible": False,
        "reason": "PRODUCT_NOT_REGISTERED",
        "recommended_slot_size": None,
    }


def test_eligible_lockers_empty(client):
    assert client.get("/api/v1/partners/p1/eligible-lockers").json() == []


def test_eligible_lockers_with_product(client):
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="LSKU",
            eligible_lockers=[
                {
                    "locker_id": "L10",
                    "locker_label": "A",
                    "recommended_slot_size": "M",
                    "slot_width_mm": 100,
                    "slot_height_mm": 100,
                    "slot_depth_mm": 100,
                    "max_weight_g": 500,
                    "temperature_zone": "AMBIENT",
                    "signature_available": True,
                    "hazardous_allowed": True,
                }
            ],
        ),
    )
    sku = client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="LSKU2",
            eligible_lockers=[
                {
                    "locker_id": "L20",
                    "recommended_slot_size": "S",
                    "slot_width_mm": 200,
                    "slot_height_mm": 200,
                    "slot_depth_mm": 200,
                    "max_weight_g": 900,
                    "temperature_zone": "AMBIENT",
                    "signature_available": True,
                    "hazardous_allowed": True,
                }
            ],
        ),
    ).json()["sku_id"]
    all_lockers = client.get("/api/v1/partners/p1/eligible-lockers").json()
    assert {x["locker_id"] for x in all_lockers} >= {"L10", "L20"}
    one = client.get(f"/api/v1/partners/p1/eligible-lockers?product_sku={sku}").json()
    assert len(one) == 1 and one[0]["locker_id"] == "L20"


def test_eligible_lockers_partner_mismatch(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="solo")).json()["sku_id"]
    assert client.get(f"/api/v1/partners/other/eligible-lockers?product_sku={sku}").status_code == 404


def test_upsert_price_changed(client, redis_client):
    redis_client.flushall()
    client.post("/api/v1/partners/p1/products", json=_body(partner_sku="u1", price_cents=100))
    client.post("/api/v1/partners/p1/products", json=_body(partner_sku="u1", price_cents=200))
    msgs = redis_client.xrange(settings.catalog_stream_key)
    types = [m[1]["event_type"] for m in msgs]
    assert "product.created" in types
    assert "product.price_changed" in types


def test_mark_deprecated(client, redis_client):
    redis_client.flushall()
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(partner_sku="dep", mark_deprecated=True),
    )
    msgs = redis_client.xrange(settings.catalog_stream_key)
    types = [m[1]["event_type"] for m in msgs]
    assert "product.created" in types
    assert "product.deprecated" in types


def test_redis_publish_failure_logged(client):
    def boom():
        raise ConnectionError("redis down")

    with mock.patch.object(publishers, "get_redis", side_effect=boom):
        with mock.patch.object(publishers.logger, "warning") as w:
            assert publishers.publish_product_created({"sku_id": "x"}) is None
            w.assert_called()


def test_check_dimensions_exceed(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body()).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 5,
            "slot_height_mm": 5,
            "slot_depth_mm": 5,
            "max_weight_g": 500,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["compatible"] is False
    assert r.json()["reason"] == "DIMENSIONS_EXCEED_LOCKER"


def test_check_weight_exceeds_locker(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body()).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 1,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "WEIGHT_EXCEEDS_LOCKER"


def test_check_signature_required(client):
    sku = client.post(
        "/api/v1/partners/p1/products",
        json=_body(compatibility_rules={"requires_signature": True, "is_fragile": False, "temperature_zone": "AMBIENT", "is_hazardous": False}),
    ).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 500,
            "temperature_zone": "AMBIENT",
            "signature_available": False,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "SIGNATURE_REQUIRED"


def test_check_hazardous_partner_rule(client):
    sku = client.post(
        "/api/v1/partners/p-restrict/products",
        json=_body(
            partner_sku="hz1",
            compatibility_rules={"requires_signature": False, "is_fragile": False, "temperature_zone": "AMBIENT", "is_hazardous": True},
        ),
    ).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 500,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "HAZARDOUS_NOT_ALLOWED"


def test_check_partner_max_weight(client):
    sku = client.post("/api/v1/partners/p-restrict/products", json=_body(partner_sku="mw", dimensions={"width_mm": 1, "height_mm": 1, "depth_mm": 1, "weight_g": 500})).json()[
        "sku_id"
    ]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 50,
            "slot_height_mm": 50,
            "slot_depth_mm": 50,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "WEIGHT_EXCEEDS_PARTNER_RULE"


def test_check_temperature_product(client):
    sku = client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            compatibility_rules={"requires_signature": False, "is_fragile": False, "temperature_zone": "FROZEN", "is_hazardous": False},
        ),
    ).json()["sku_id"]
    db = SessionLocal()
    try:
        db.add(
            PartnerProductRule(
                partner_id="p1",
                category_id="CAT",
                allowed_temperature_zones_json='["AMBIENT"]',
                max_weight_g=None,
                requires_signature=None,
                is_hazardous_allowed=None,
                overrides_global=True,
            )
        )
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "TEMPERATURE_ZONE_NOT_ALLOWED_FOR_PRODUCT"


def test_check_temperature_locker(client):
    db = SessionLocal()
    try:
        db.add(
            PartnerProductRule(
                partner_id="p1",
                category_id=None,
                allowed_temperature_zones_json='["AMBIENT"]',
                max_weight_g=None,
                requires_signature=None,
                is_hazardous_allowed=None,
                overrides_global=False,
            )
        )
        db.commit()
    finally:
        db.close()
    sku = client.post("/api/v1/partners/p1/products", json=_body()).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "FROZEN",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "TEMPERATURE_ZONE_NOT_ALLOWED_FOR_LOCKER"


def test_check_inactive_product(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="ina")).json()["sku_id"]
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.sku_id == sku).one()
        p.is_active = False
        db.add(p)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "PRODUCT_INACTIVE"


def test_check_deprecated_product(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="dep2")).json()["sku_id"]
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.sku_id == sku).one()
        p.is_deprecated = True
        db.add(p)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "PRODUCT_DEPRECATED"


def test_check_dimensions_missing(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="nodim")).json()["sku_id"]
    db = SessionLocal()
    try:
        from models import ProductDimensions

        db.query(ProductDimensions).filter(ProductDimensions.product_id == sku).delete()
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "DIMENSIONS_MISSING"


def test_create_eligible_lockers_none_fit(client):
    r = client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="badfit",
            eligible_lockers=[
                {
                    "locker_id": "x",
                    "slot_width_mm": 1,
                    "slot_height_mm": 1,
                    "slot_depth_mm": 1,
                    "max_weight_g": 500,
                    "temperature_zone": "AMBIENT",
                    "signature_available": True,
                    "hazardous_allowed": True,
                }
            ],
        ),
    )
    assert r.status_code == 400


def test_create_eligible_lockers_only_none_dims_ok(client):
    r = client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="nodimslock",
            eligible_lockers=[{"locker_id": "z1"}],
        ),
    )
    assert r.status_code == 201


def test_get_product_bad_images_json(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="img")).json()["sku_id"]
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.sku_id == sku).one()
        p.images_json = "not-json-array"
        db.add(p)
        db.commit()
    finally:
        db.close()
    g = client.get(f"/api/v1/products/{sku}")
    assert g.json()["images"] == []


def test_partner_rule_signature_override(client):
    db = SessionLocal()
    try:
        db.add(
            PartnerProductRule(
                partner_id="p1",
                category_id="CAT",
                allowed_temperature_zones_json='["AMBIENT","FROZEN"]',
                max_weight_g=None,
                requires_signature=True,
                is_hazardous_allowed=None,
                overrides_global=True,
            )
        )
        db.commit()
    finally:
        db.close()
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="sigov")).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": False,
            "hazardous_allowed": True,
        },
    )
    assert r.json()["reason"] == "SIGNATURE_REQUIRED"


def test_effective_temperature_zones_bad_json():
    from services import compatibility_service
    from models import PartnerProductRule

    rule = PartnerProductRule(
        partner_id="x",
        category_id=None,
        allowed_temperature_zones_json="not-json",
        max_weight_g=None,
        requires_signature=None,
        is_hazardous_allowed=None,
        overrides_global=False,
    )
    z = compatibility_service.effective_allowed_temperature_zones(rule)
    assert "AMBIENT" in z


def test_recommended_slot_sizes():
    from services import compatibility_service

    assert compatibility_service._recommended_slot_size(10, 10, 10) == "S"
    assert compatibility_service._recommended_slot_size(100, 100, 100) == "M"
    assert compatibility_service._recommended_slot_size(500, 500, 500) == "L"


def test_publishers_get_redis_lazy_connect(redis_client):
    import fakeredis

    publishers.set_redis_client(None)
    fake = fakeredis.FakeRedis(decode_responses=True)
    with mock.patch("events.publishers.redis.from_url", return_value=fake):
        assert publishers.get_redis() is fake
        assert publishers.get_redis() is fake
    publishers.set_redis_client(redis_client)


def test_upsert_mark_deprecated_existing(client, redis_client):
    redis_client.flushall()
    client.post("/api/v1/partners/p1/products", json=_body(partner_sku="depup", price_cents=50))
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(partner_sku="depup", price_cents=50, mark_deprecated=True),
    )
    types = [m[1]["event_type"] for m in redis_client.xrange(settings.catalog_stream_key)]
    assert "product.deprecated" in types


def test_upsert_recreates_dimensions(client):
    sku = client.post("/api/v1/partners/p1/products", json=_body(partner_sku="redim")).json()["sku_id"]
    db = SessionLocal()
    try:
        from models import ProductDimensions

        db.query(ProductDimensions).filter(ProductDimensions.product_id == sku).delete()
        db.commit()
    finally:
        db.close()
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(partner_sku="redim", dimensions={"width_mm": 5, "height_mm": 5, "depth_mm": 5, "weight_g": 5}),
    )
    g = client.get(f"/api/v1/products/{sku}")
    assert g.json()["dimensions"]["width_mm"] == 5


def test_eligible_lockers_dedupes_duplicate_locker_rows(client):
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="d1",
            eligible_lockers=[
                {
                    "locker_id": "DUP",
                    "slot_width_mm": 200,
                    "slot_height_mm": 200,
                    "slot_depth_mm": 200,
                    "max_weight_g": 900,
                    "temperature_zone": "AMBIENT",
                    "signature_available": True,
                    "hazardous_allowed": True,
                },
                {
                    "locker_id": "DUP",
                    "slot_width_mm": 300,
                    "slot_height_mm": 300,
                    "slot_depth_mm": 300,
                    "max_weight_g": 900,
                    "temperature_zone": "AMBIENT",
                    "signature_available": True,
                    "hazardous_allowed": True,
                },
            ],
        ),
    )
    rows = client.get("/api/v1/partners/p1/eligible-lockers").json()
    assert len([x for x in rows if x["locker_id"] == "DUP"]) == 1


def test_upsert_price_and_deprecate_same_request(client, redis_client):
    redis_client.flushall()
    client.post("/api/v1/partners/p1/products", json=_body(partner_sku="both", price_cents=10))
    client.post(
        "/api/v1/partners/p1/products",
        json=_body(partner_sku="both", price_cents=99, mark_deprecated=True),
    )
    types = [m[1]["event_type"] for m in redis_client.xrange(settings.catalog_stream_key)]
    assert types.count("product.price_changed") >= 1
    assert types.count("product.deprecated") >= 1


def test_product_detail_images_validator_variants():
    from datetime import datetime, timezone

    from schemas import OrderPickupProductCacheDTO, ProductDetailOut

    now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    cache = OrderPickupProductCacheDTO(
        sku_id="s",
        partner_id="p",
        partner_sku="ps",
        name="n",
        description=None,
        category_id="CAT",
        amount_cents=1,
        currency="BRL",
        width_mm=None,
        height_mm=None,
        depth_mm=None,
        weight_g=None,
        is_active=True,
        requires_signature=False,
        is_hazardous=False,
        temperature_zone="AMBIENT",
        created_at=now,
        updated_at=now,
        synced_at=None,
    )
    base = {
        "sku_id": "s",
        "partner_id": "p",
        "partner_sku": "ps",
        "name": "n",
        "description": None,
        "category_id": "CAT",
        "amount_cents": 1,
        "currency": "BRL",
        "is_active": True,
        "is_deprecated": False,
        "requires_signature": False,
        "is_fragile": False,
        "is_hazardous": False,
        "temperature_zone": "AMBIENT",
        "dimensions": None,
        "order_pickup_cache": cache.model_dump(mode="python"),
        "created_at": now,
        "updated_at": now,
    }
    a = ProductDetailOut.model_validate({**base, "images": '["http://a"]'})
    assert a.images == ["http://a"]
    b = ProductDetailOut.model_validate({**base, "images": "{}"})
    assert b.images == []
    c = ProductDetailOut.model_validate({**base, "images": None})
    assert c.images == []
    d = ProductDetailOut.model_validate({**base, "images": ["z"]})
    assert d.images == ["z"]
    e = ProductDetailOut.model_validate({**base, "images": "not-json"})
    assert e.images == []


def test_hazardous_locker_denies(client):
    sku = client.post(
        "/api/v1/partners/p1/products",
        json=_body(
            partner_sku="hzloc",
            compatibility_rules={"requires_signature": False, "is_fragile": False, "temperature_zone": "AMBIENT", "is_hazardous": True},
        ),
    ).json()["sku_id"]
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={
            "locker_id": "L1",
            "slot_width_mm": 200,
            "slot_height_mm": 200,
            "slot_depth_mm": 200,
            "max_weight_g": 900,
            "temperature_zone": "AMBIENT",
            "signature_available": True,
            "hazardous_allowed": False,
        },
    )
    assert r.json()["reason"] == "HAZARDOUS_NOT_ALLOWED"
