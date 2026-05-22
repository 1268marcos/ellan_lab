from __future__ import annotations

from unittest.mock import patch

from app.core.database import SessionLocal
from app.services import capability_webhook_service as svc
from app.services import webhook_dlq


def test_marketplace_dead_letter_replay(client):
    client.post("/api/v1/marketplace-admin/channel-partners/seed-players")
    client.post("/api/v1/marketplace-admin/capability-webhooks/seed-from-catalog")
    db = SessionLocal()
    try:
        hooks = svc.list_capability_webhooks(db)
        assert hooks
        wh = hooks[0]
        with patch(
            "app.services.capability_webhook_service.dispatch_webhook",
            return_value=(False, 500, "fail"),
        ):
            for _ in range(3):
                svc.deliver_event(db, wh, "webhook.test", {"x": 1}, force=True)
        dlq = svc.list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER)
        assert dlq
        with patch(
            "app.services.capability_webhook_service.dispatch_webhook",
            return_value=(True, 200, "ok"),
        ):
            r = svc.replay_delivery(db, dlq[0].id)
        assert r.success
    finally:
        db.close()
