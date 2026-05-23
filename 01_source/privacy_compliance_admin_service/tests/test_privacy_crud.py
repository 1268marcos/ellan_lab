from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_seed_and_dashboard(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["regulations"] >= 15

    r = client.get(f"{API}/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["regulations"] >= 15
    assert body["active_policies"] >= 7


def test_regulations_crud(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/regulations",
        json={
            "code": "NZ_PA",
            "name": "Privacy Act 2020 (New Zealand)",
            "jurisdiction": "NZ",
            "default_retention_days": 365,
            "response_sla_days": 30,
        },
    )
    assert r.status_code == 201
    reg_id = r.json()["id"]

    r = client.patch(f"{API}/regulations/{reg_id}", json={"active": False})
    assert r.status_code == 200
    assert r.json()["active"] is False

    r = client.get(f"{API}/regulations")
    assert r.status_code == 200
    assert r.json()["total"] >= 4

    r = client.delete(f"{API}/regulations/{reg_id}")
    assert r.status_code == 204


def test_consents_deletions_subject_requests_webhooks_api_keys(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/consents",
        json={
            "regulation_code": "GDPR",
            "consent_type": "TELEMETRY",
            "granted": True,
            "user_id": "usr-test-01",
            "channel": "KIOSK",
            "policy_version": "3.0",
        },
    )
    assert r.status_code == 201
    consent_id = r.json()["id"]

    r = client.patch(f"{API}/consents/{consent_id}", json={"granted": False})
    assert r.status_code == 200
    assert r.json()["revoked_at"] is not None

    r = client.post(
        f"{API}/deletion-requests",
        json={
            "regulation_code": "LGPD",
            "user_id": "usr-test-br",
            "reason": "Titular solicitou eliminação",
        },
    )
    assert r.status_code == 201
    del_id = r.json()["id"]

    r = client.patch(f"{API}/deletion-requests/{del_id}", json={"status": "COMPLETED"})
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"

    r = client.post(
        f"{API}/subject-requests",
        json={
            "regulation_code": "CCPA",
            "request_type": "PORTABILITY",
            "user_id": "usr-test-us",
            "details": "Export locker pickup history",
        },
    )
    assert r.status_code == 201
    assert r.json()["due_at"] is not None

    r = client.put(
        f"{API}/webhooks",
        json={
            "regulation_code": "CCPA",
            "url": "https://hooks.test.local/privacy/ccpa",
            "events": ["dsar.completed", "deletion.completed"],
            "secret": "whsec-test-ccpa",
        },
    )
    assert r.status_code == 200
    assert "CCPA" in r.json()["regulation_code"]

    r = client.post(f"{API}/regulations/GDPR/api-keys/rotate")
    assert r.status_code == 200
    assert "api_key" in r.json()

    r = client.get(f"{API}/regulations/GDPR/api-keys")
    assert r.status_code == 200
    assert len(r.json()["keys"]) >= 1

    r = client.get(f"{API}/policy-versions")
    assert r.status_code == 200
    assert r.json()["total"] >= 3
