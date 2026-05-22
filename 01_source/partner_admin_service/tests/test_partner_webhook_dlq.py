from __future__ import annotations

from unittest.mock import patch

from app.core.database import SessionLocal
from app.models.partner_capability_webhook import PartnerCapabilityWebhookDelivery
from app.services import partner_capability_webhook_service as svc
from app.services import webhook_dlq
from app.services.crypto_util import new_id


def _bootstrap(client):
    client.post("/api/v1/partner-admin/ecosystem/players/sync-catalog")
    client.post("/api/v1/partner-admin/ecosystem/players/seed-professional")
    client.post("/api/v1/partner-admin/ecosystem/capability-webhooks/mirror-from-capabilities")


def test_dead_letter_after_failures_and_replay(client):
    _bootstrap(client)
    db = SessionLocal()
    try:
        wh = svc.list_capability_webhooks(db)[0]
        with patch(
            "app.services.partner_capability_webhook_service.dispatch_webhook",
            return_value=(False, 500, "simulated_failure"),
        ):
            for _ in range(3):
                svc.deliver_event(db, wh, "webhook.test", {"fail": True}, force=True)
        dlq = svc.list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER)
        assert len(dlq) >= 1
        with patch(
            "app.services.partner_capability_webhook_service.dispatch_webhook",
            return_value=(True, 200, "ok"),
        ):
            replayed = svc.replay_delivery(db, dlq[0].id)
        assert replayed.success is True
        assert replayed.status == webhook_dlq.STATUS_DELIVERED
        assert replayed.replay_of_delivery_id == dlq[0].id
    finally:
        db.close()


def test_replay_dead_letter_batch_endpoint(client):
    _bootstrap(client)
    db = SessionLocal()
    try:
        wh = svc.list_capability_webhooks(db)[0]
        for i in range(2):
            db.add(
                PartnerCapabilityWebhookDelivery(
                    id=new_id(),
                    webhook_id=wh.id,
                    event_type="webhook.test",
                    payload_json=f'{{"n":{i}}}',
                    success=False,
                    status=webhook_dlq.STATUS_DEAD_LETTER,
                    attempt_count=3,
                    dead_lettered_at=svc._utcnow(),
                )
            )
        db.commit()
    finally:
        db.close()

    r = client.post("/api/v1/partner-admin/ecosystem/capability-webhooks/deliveries/replay-dead-letter?limit=5")
    assert r.status_code == 200
    assert r.json()["replayed"] >= 1


def test_certification_mirror_and_corridor_sla(client):
    _bootstrap(client)
    client.post("/api/v1/partner-admin/ecosystem/global-ops/seed")
    mirror = client.post("/api/v1/partner-admin/ecosystem/global-ops/certifications/mirror")
    assert mirror.status_code == 200
    sla = client.get("/api/v1/partner-admin/ecosystem/global-ops/corridor-sla")
    assert sla.status_code == 200
    assert len(sla.json()) >= 4
