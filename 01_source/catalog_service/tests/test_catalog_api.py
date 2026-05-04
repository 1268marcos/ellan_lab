from __future__ import annotations

import json

PID = "11111111-1111-1111-1111-111111111111"


def _create(client, sku="SH1"):
    return client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": sku,
            "name": "Item",
            "description": "d",
            "category_id": "GENERAL",
            "dimensions": {"width_mm": 10, "height_mm": 10, "depth_mm": 10, "weight_g": 100},
            "price_cents": 1000,
            "currency": "BRL",
            "images": [],
            "compatibility_rules": {
                "requires_signature": False,
                "is_fragile": False,
                "temperature_zone": "AMBIENT",
            },
        },
    )


def test_create_product(client):
    r = _create(client)
    assert r.status_code == 201
    assert r.json()["sku_id"]
    assert r.json()["version"] == 1


def test_bulk_create(client):
    r = client.post(
        "/api/v1/products/bulk",
        json={
            "partner_id": PID,
            "items": [
                {
                    "partner_sku": "B1",
                    "name": "Bulk1",
                    "category_id": "GENERAL",
                    "price_cents": 1,
                    "dimensions": {"weight_g": 1},
                }
            ],
        },
    )
    assert r.status_code == 200
    assert len(r.json()["created"]) == 1


def test_get_product_cached(client):
    sku = _create(client).json()["sku_id"]
    r1 = client.get(f"/api/v1/products/{sku}")
    assert r1.status_code == 200
    assert r1.headers.get("X-DTO-Version") == "v1"
    assert r1.headers.get("X-Cache") in ("MISS", "HIT")
    r2 = client.get(f"/api/v1/products/{sku}")
    assert r2.headers.get("X-Cache") == "HIT"


def test_product_versions(client):
    sku = _create(client).json()["sku_id"]
    r = client.get(f"/api/v1/products/{sku}/versions")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_eligible_lockers(client):
    r = client.get(f"/api/v1/partners/{PID}/eligible-lockers")
    assert r.status_code == 200
    assert len(r.json()["lockers"]) >= 1


def test_create_duplicate(client):
    _create(client, "DUP")
    r = _create(client, "DUP")
    assert r.status_code == 400


def test_category_missing(client):
    r = client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": "X",
            "name": "n",
            "category_id": "NOCAT",
            "price_cents": 1,
            "dimensions": {},
        },
    )
    assert r.status_code == 404


def test_get_404(client):
    assert client.get("/api/v1/products/00000000-0000-0000-0000-000000000099").status_code == 404


def test_versions_404(client):
    assert client.get("/api/v1/products/00000000-0000-0000-0000-000000000099/versions").status_code == 404


def test_categories_list(client):
    r = client.get("/api/v1/categories")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "catalog-service"


def test_order_pickup_cache_shape(client):
    sku = _create(client).json()["sku_id"]
    body = client.get(f"/api/v1/products/{sku}").json()
    assert "order_pickup_cache" in body
    assert body["order_pickup_cache"]["amount_cents"] == 1000


def test_eligible_lockers_filter_by_product(client):
    _create(client, "HEAVY")
    r = client.get(f"/api/v1/partners/{PID}/eligible-lockers?product_sku=HEAVY")
    assert r.status_code == 200
