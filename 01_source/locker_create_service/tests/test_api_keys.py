from __future__ import annotations

API = "/api/v1/locker-create/lockers"


def _create(client):
    client.post(
        API,
        json={
            "id": "LK-KEY-001",
            "display_name": "Key Locker",
            "region": "SP",
            "city": "Osasco",
            "state": "SP",
        },
    )


def test_rotate_and_list_keys(client):
    _create(client)
    r = client.post(f"{API}/LK-KEY-001/api-keys/rotate")
    assert r.status_code == 200
    key = r.json()["api_key"]
    assert key.startswith("lk_")

    r = client.post(f"{API}/LK-KEY-001/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"] != key

    r = client.get(f"{API}/LK-KEY-001/api-keys")
    assert r.status_code == 200
    keys = r.json()["keys"]
    assert len(keys) == 2
    assert sum(1 for k in keys if k["active"]) == 1
