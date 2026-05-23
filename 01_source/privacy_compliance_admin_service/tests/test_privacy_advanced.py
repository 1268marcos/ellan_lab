from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_transfer_wizard_scc_flow(client):
    client.post(f"{API}/seed")

    r = client.post(f"{API}/transfer-wizard/sessions", json={"regulation_code": "GDPR"})
    assert r.status_code == 201
    session = r.json()
    sid = session["id"]
    assert session["current_step"] == "SCOPE"

    r = client.patch(
        f"{API}/transfer-wizard/sessions/{sid}/step",
        json={"step": "SCOPE", "destination_country": "US"},
    )
    assert r.status_code == 200
    assert r.json()["current_step"] == "MECHANISM"

    r = client.patch(
        f"{API}/transfer-wizard/sessions/{sid}/step",
        json={"step": "MECHANISM", "mechanism": "SCC", "adequacy_notes": "Module 2 + Module 3"},
    )
    assert r.status_code == 200

    r = client.patch(
        f"{API}/transfer-wizard/sessions/{sid}/step",
        json={"step": "PROCESSOR", "processor_id": "proc-demo"},
    )
    assert r.status_code == 200

    r = client.patch(
        f"{API}/transfer-wizard/sessions/{sid}/step",
        json={"step": "DOCUMENT", "document_ref": "SCC-2026-INPOST-US"},
    )
    assert r.status_code == 200
    assert r.json()["current_step"] == "REVIEW"

    r = client.post(f"{API}/transfer-wizard/sessions/{sid}/complete")
    assert r.status_code == 200
    transfer = r.json()
    assert transfer["destination_country"] == "US"
    assert transfer["mechanism"] == "SCC"


def test_webhook_dispatch_and_dlq(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/webhooks/dispatch",
        json={
            "regulation_code": "GDPR",
            "event_name": "consent.granted",
            "payload": {"demo": True},
            "aggregate_id": "cons-test-001",
        },
    )
    assert r.status_code == 201
    delivery = r.json()
    assert delivery["status"] == "DELIVERED"
    assert delivery["last_status_code"] == 202

    r = client.get(f"{API}/webhook-deliveries?regulation_code=GDPR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_global_ops_certifications_bridge(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/ecosystem/global-ops-bridge")
    assert r.status_code == 200
    bridge = r.json()
    assert bridge["certifications_cached"] >= 5

    r = client.get(f"{API}/ecosystem/certifications?player_code=INPOST")
    assert r.status_code == 200
    certs = r.json()
    assert certs["total"] >= 1
    types = {c["certification_type"] for c in certs["items"]}
    assert "ISO27001" in types or "GDPR_DPA" in types

    r = client.post(f"{API}/ecosystem/certifications/sync")
    assert r.status_code == 200
    assert r.json()["synced"] >= 1
