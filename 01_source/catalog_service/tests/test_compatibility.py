from __future__ import annotations

PID = "11111111-1111-1111-1111-111111111111"


def _mk(client, sku="C1"):
    return client.post(
        f"/api/v1/partners/{PID}/products",
        json={
            "partner_sku": sku,
            "name": "C",
            "category_id": "GENERAL",
            "dimensions": {"weight_g": 100},
            "price_cents": 1,
            "compatibility_rules": {"temperature_zone": "AMBIENT"},
        },
    ).json()["sku_id"]


def test_check_by_partner_sku(client):
    _mk(client)
    r = client.post(
        f"/api/v1/partners/{PID}/check-compatibility",
        json={"partner_sku": "C1", "locker_id": "locker-m-001"},
    )
    assert r.status_code == 200
    assert r.json()["compatible"] is True


def test_check_unknown_product(client):
    r = client.post(
        f"/api/v1/partners/{PID}/check-compatibility",
        json={"partner_sku": "NOSUCH", "locker_id": "locker-m-001"},
    )
    assert r.json()["compatible"] is False
    assert r.json()["reason"] == "PRODUCT_NOT_REGISTERED"


def test_check_by_canonical_sku(client):
    sku = _mk(client, "C2")
    r = client.post(
        f"/api/v1/products/{sku}/check-compatibility",
        json={"locker_spec": {"slot_size": "M", "max_weight_g": 5000}},
    )
    assert r.json()["compatible"] is True


def test_check_canonical_unknown(client):
    r = client.post(
        "/api/v1/products/00000000-0000-0000-0000-000000000099/check-compatibility",
        json={"locker_spec": {"slot_size": "M", "max_weight_g": 5000}},
    )
    assert r.json()["reason"] == "PRODUCT_NOT_REGISTERED"


def test_check_bad_locker(client):
    _mk(client, "C3")
    r = client.post(
        f"/api/v1/partners/{PID}/check-compatibility",
        json={"partner_sku": "C3", "locker_id": "missing-locker"},
    )
    body = r.json()
    assert body["compatible"] is False
