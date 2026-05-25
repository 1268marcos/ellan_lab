from __future__ import annotations

API = "/api/v1/hardware-admin"
VENDORS = f"{API}/hardware-vendors"
ASSETS = f"{API}/hardware-assets"
OPERATORS = f"{API}/locker-operators"
RUNTIME = f"{API}/runtime-lockers"
OPS = f"{API}/hardware-ops"


def test_seed_and_vendor_crud(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["vendors"] >= 1

    r = client.get(VENDORS)
    assert r.status_code == 200
    assert r.json()["total"] >= 7

    r = client.post(
        VENDORS,
        json={
            "id": "hw-v-test",
            "name": "Test Vendor",
            "code": "TEST-VENDOR",
            "vendor_type": "LOCKER_NETWORK",
            "region_code": "BR",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{VENDORS}/hw-v-test/webhook",
        json={"url": "https://hooks.example/hardware", "secret": "whsec_hw"},
    )
    assert r.status_code == 200

    r = client.post(f"{VENDORS}/hw-v-test/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("hw_")


def test_asset_and_operator_crud(client):
    client.post(f"{API}/seed")

    r = client.get(ASSETS)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        ASSETS,
        json={
             "asset_code": "EHA-TEST-01",
            "asset_category": "SENSOR",
            "description": "Sensor temperatura",
            "acquisition_date": "2025-01-15",
            "acquisition_cost_cents": 12000,
            "useful_life_months": 36,
        },
    )
    assert r.status_code == 201
    asset_id = r.json()["id"]

    r = client.patch(f"{ASSETS}/{asset_id}", json={"status": "INACTIVE"})
    assert r.status_code == 200

    r = client.get(OPERATORS)
    assert r.status_code == 200
    assert r.json()["total"] >= 4


def test_runtime_and_ops(client):
    client.post(f"{API}/seed")

    r = client.get(RUNTIME)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{OPS}/devices")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{OPS}/sync-queue")
    assert r.status_code == 200

    r = client.get(f"{OPS}/telemetry")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
