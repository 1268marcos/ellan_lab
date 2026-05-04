from __future__ import annotations

from app.services import cache_service

PID = "11111111-1111-1111-1111-111111111111"


def test_cache_invalidation(client, fake_redis):
    sku = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "CACHE1",
            "name": "c",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 1},
            "price_cents": 100,
        },
    ).json()["sku_id"]
    assert client.get(f"/api/v1/products/{sku}").headers.get("X-Cache") == "HIT"
    cache_service.invalidate_product(fake_redis, sku)
    assert client.get(f"/api/v1/products/{sku}").headers.get("X-Cache") == "MISS"


def test_corrupt_cache_invalidates(client, fake_redis):
    sku = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "CACHE2",
            "name": "c",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 1},
            "price_cents": 100,
        },
    ).json()["sku_id"]
    client.get(f"/api/v1/products/{sku}")
    fake_redis.set(cache_service.cache_key_product(sku), "not-json")
    r = client.get(f"/api/v1/products/{sku}")
    assert r.status_code == 200
