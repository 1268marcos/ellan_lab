from __future__ import annotations


def test_marketplace_global_ops_seed(client):
    client.post("/api/v1/marketplace-admin/channel-partners/seed-players")
    r = client.post("/api/v1/marketplace-admin/global-ops/seed")
    assert r.status_code == 200
    data = r.json()
    assert data["certifications"] >= 8
    assert data["corridors"] >= 3

    s = client.get("/api/v1/marketplace-admin/global-ops/summary")
    assert s.status_code == 200
    assert s.json()["corridors_active"] >= 1

    corridors = client.get("/api/v1/marketplace-admin/global-ops/corridors?origin=BR")
    assert corridors.status_code == 200
    items = corridors.json()
    assert any(c["corridor_code"] == "BR-BR-LOCKER-NATIONAL" for c in items)
    assert items[0].get("steps")
