from __future__ import annotations

from unittest.mock import patch

from app.core.database import SessionLocal
from app.models.professional_ops import HardwareCapabilityWebhook, HardwareSyncAuditLog
from app.services import capability_webhook_service as wh_svc
from app.services import professional_ops_service
from app.services import webhook_dlq

API = "/api/v1/hardware-admin"
PRO = f"{API}/professional-ops"

MOCK_MKT_CERTS = [
    {
        "id": "mkt-cert-inpost-ce",
        "partner_code": "INPOST",
        "certification_type": "CE_MARK",
        "status": "VALID",
        "issuer": "TÜV SÜD",
        "issued_at": "2024-01-15",
        "expires_at": "2027-01-15",
        "evidence_url": "https://compliance.example/inpost/ce_mark",
    },
    {
        "id": "mkt-cert-magalu-pci",
        "partner_code": "MAGALU",
        "certification_type": "PCI_DSS",
        "status": "VALID",
        "issuer": "Visa CISP",
        "issued_at": "2024-01-01",
        "expires_at": "2025-12-31",
        "evidence_url": None,
    },
    {
        "id": "mkt-cert-unknown",
        "partner_code": "UNKNOWN_PARTNER_X",
        "certification_type": "ISO27001",
        "status": "VALID",
        "issuer": "BSI",
        "issued_at": None,
        "expires_at": None,
        "evidence_url": None,
    },
]


def test_webhook_dlq_and_replay(client):
    client.post(f"{API}/seed")
    client.post(f"{PRO}/capability-webhooks/seed-dlq-demo")

    r = client.get(f"{PRO}/capability-webhooks/deliveries?status=DEAD_LETTER")
    assert r.status_code == 200
    dlq = r.json()["items"]
    assert len(dlq) >= 1

    with patch(
        "app.services.capability_webhook_service.dispatch_webhook",
        return_value=(True, 200, "ok"),
    ):
        r2 = client.post(f"{PRO}/capability-webhooks/deliveries/{dlq[0]['id']}/replay")
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    r3 = client.post(f"{PRO}/capability-webhooks/deliveries/replay-dead-letter?limit=5")
    assert r3.status_code == 200
    assert "replayed" in r3.json()


def test_mirror_certifications_from_marketplace_http(client):
    client.post(f"{API}/seed")

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return MOCK_MKT_CERTS

    with patch("httpx.Client.get", return_value=FakeResp()):
        r = client.post(f"{PRO}/certifications/mirror-marketplace")
    assert r.status_code == 200
    body = r.json()
    assert body["fetched"] == 3
    assert body["inserted"] + body["updated"] >= 2
    assert body["skipped"] >= 1

    r2 = client.get(f"{PRO}/certifications?player_code=INPOST")
    assert r2.status_code == 200
    types = {c["certification_type"] for c in r2.json()["items"]}
    assert "CE_MARK" in types
    mirrored = [c for c in r2.json()["items"] if c.get("source") == "MARKETPLACE_MIRROR"]
    assert mirrored

    # idempotente
    with patch("httpx.Client.get", return_value=FakeResp()):
        r3 = client.post(f"{PRO}/certifications/mirror-marketplace")
    assert r3.status_code == 200
    assert r3.json()["inserted"] == 0

    db = SessionLocal()
    try:
        logs = db.query(HardwareSyncAuditLog).filter_by(event_type="CERT_MIRROR").count()
        assert logs >= 1
    finally:
        db.close()


def test_webhook_dlq_unit(client):
    client.post(f"{API}/seed")
    db = SessionLocal()
    try:
        hooks = db.query(HardwareCapabilityWebhook).all()
        assert hooks
        wh = hooks[0]
        with patch("app.services.capability_webhook_service.dispatch_webhook", return_value=(False, 500, "fail")):
            for _ in range(3):
                wh_svc.deliver_event(db, wh, "webhook.test", {"x": 1}, force=True)
        dlq = wh_svc.list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER)
        assert dlq
    finally:
        db.close()
