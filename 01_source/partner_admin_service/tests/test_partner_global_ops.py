from __future__ import annotations


def _bootstrap_ecosystem(client):
    client.post("/api/v1/partner-admin/ecosystem/players/sync-catalog")
    client.post("/api/v1/partner-admin/ecosystem/players/seed-professional")
    client.post("/api/v1/partner-admin/ecosystem/global-ops/seed")


def test_global_ops_seed_and_summary(client):
    _bootstrap_ecosystem(client)
    r = client.post("/api/v1/partner-admin/ecosystem/global-ops/seed")
    assert r.status_code == 200
    data = r.json()
    assert data["certifications"] >= 10
    assert data["corridors"] >= 4
    assert data["readiness_rows"] >= 1

    s = client.get("/api/v1/partner-admin/ecosystem/global-ops/summary")
    assert s.status_code == 200
    body = s.json()
    assert body["certifications_valid"] >= 10
    assert body["corridors_active"] >= 4


def test_global_ops_lists(client):
    _bootstrap_ecosystem(client)
    client.post("/api/v1/partner-admin/ecosystem/global-ops/seed")

    certs = client.get("/api/v1/partner-admin/ecosystem/global-ops/certifications?player_code=INPOST")
    assert certs.status_code == 200
    assert any(c["certification_type"] == "ISO27001" for c in certs.json())

    corridors = client.get("/api/v1/partner-admin/ecosystem/global-ops/corridors?origin=BR")
    assert corridors.status_code == 200
    assert any(c["corridor_code"] == "BR-BR-LOCKER-NATIONAL" for c in corridors.json())

    readiness = client.get("/api/v1/partner-admin/ecosystem/global-ops/readiness?limit=5")
    assert readiness.status_code == 200
    assert len(readiness.json()) >= 1

    health = client.get("/api/v1/partner-admin/ecosystem/global-ops/relation-health")
    assert health.status_code == 200
    assert len(health.json()) >= 1
