from __future__ import annotations

API = "/api/v1/locker-create/lockers"


def _payload(locker_id: str = "PR-CAPITAL-SANTAFELICIDADE-LK-001") -> dict:
    return {
        "id": locker_id,
        "display_name": "Curitiba Santa Felicidade - Locker 001",
        "region": "PR",
        "city": "Curitiba",
        "state": "PR",
        "country": "BR",
        "timezone": "America/Sao_Paulo",
        "operator_id": "OP-ELLAN-001",
        "temperature_zone": "AMBIENT",
        "security_level": "STANDARD",
        "has_kiosk": True,
        "has_card_reader": True,
    }


def test_create_list_get_patch_delete(client):
    r = client.post(API, json=_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "PR-CAPITAL-SANTAFELICIDADE-LK-001"
    assert body["slots_count"] == 30
    assert len(body["slot_configs"]) == 3

    r = client.get(API)
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = client.get(f"{API}/PR-CAPITAL-SANTAFELICIDADE-LK-001")
    assert r.status_code == 200

    r = client.patch(f"{API}/PR-CAPITAL-SANTAFELICIDADE-LK-001", json={"active": False})
    assert r.status_code == 200
    assert r.json()["active"] is False

    r = client.delete(f"{API}/PR-CAPITAL-SANTAFELICIDADE-LK-001")
    assert r.status_code == 204

    r = client.get(f"{API}/PR-CAPITAL-SANTAFELICIDADE-LK-001")
    assert r.status_code == 404


def test_bulk_create_partial_failure(client):
    client.post(API, json=_payload("LK-BASE-001"))
    r = client.post(
        f"{API}/bulk",
        json={
            "lockers": [
                _payload("LK-BULK-001"),
                _payload("LK-BASE-001"),
            ]
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data["created"]) == 1
    assert len(data["failed"]) == 1
