from __future__ import annotations

from unittest import mock

import httpx

from app.services import webhook_service

PID = "11111111-1111-1111-1111-111111111111"


def test_webhook_delivery(client, fake_redis):
    client.post(
        f"/api/v1/partners/{PID}/webhooks",
        json={"url": "https://example.com/hook", "secret": "s", "events": ["product.created"]},
    )
    class MC:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 200
            r.is_success = True
            r.text = ""
            return r

    with mock.patch.object(httpx, "Client", lambda **k: MC()):
        client.post(
            f"/api/v1/partners/{PID}/products",
            json={
                "partner_sku": "WH1",
                "name": "w",
                "category_id": "GENERAL",
                "dimensions": {"weight_g": 1},
                "price_cents": 1,
            },
        )


def test_webhook_deliver_fail():
    code, err = webhook_service.deliver_sync("http://invalid.local/x", None, "t", {})
    assert code == 0
    assert err


def test_webhook_notify_filtered(fake_redis):
    webhook_service.configure_webhook(fake_redis, partner_id="p1", url="http://x", secret=None, events=["other"])
    webhook_service.notify_partner(fake_redis, "p1", "product.created", {})
