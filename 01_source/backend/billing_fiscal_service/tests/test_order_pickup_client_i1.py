# I-1 — fallback fiscal-context → invoice-source → /status?full_fiscal=1
from __future__ import annotations

from unittest.mock import patch

from app.integrations.order_pickup_client import (
    OrderPickupClientError,
    get_order_snapshot_for_invoice,
)


def _v2_payload(order_id: str = "ord_1") -> dict:
    return {
        "ok": True,
        "contract_version": 2,
        "order": {"id": order_id, "region": "BR-SP", "totem_id": "t1"},
        "order_items": [{"sku_id": "A", "quantity": 1, "unit_amount_cents": 100, "total_amount_cents": 100}],
        "allocation": None,
        "pickup": None,
        "locker_id": "L1",
        "locker_address": {"city": "São Paulo"},
        "tenant_fiscal": {"cnpj": "123"},
        "tenant_cnpj": "123",
        "tenant_razao_social": "X",
        "consumer_cpf": None,
        "consumer_name": None,
    }


def test_fiscal_context_success_maps_v2():
    with patch(
        "app.integrations.order_pickup_client.get_order_fiscal_context",
        return_value=_v2_payload(),
    ), patch("app.integrations.order_pickup_client.get_order_snapshot") as snap:
        out = get_order_snapshot_for_invoice("ord_1")
    snap.assert_not_called()
    assert out["contract_version"] == 2
    assert out["order_items"][0]["sku_id"] == "A"


def test_transport_error_falls_back_to_invoice_source():
    with patch(
        "app.integrations.order_pickup_client.get_order_fiscal_context",
        side_effect=OrderPickupClientError("Falha ao consultar order_pickup_service: HTTPConnectionPool"),
    ), patch(
        "app.integrations.order_pickup_client.get_order_invoice_source",
        return_value=_v2_payload(),
    ), patch("app.integrations.order_pickup_client.get_order_snapshot") as snap:
        out = get_order_snapshot_for_invoice("ord_1")
    snap.assert_not_called()
    assert out["locker_id"] == "L1"


def test_transport_error_invoice_source_fails_then_status():
    status_wrap = {"ok": True, **_v2_payload()}
    with patch(
        "app.integrations.order_pickup_client.get_order_fiscal_context",
        side_effect=OrderPickupClientError("Read timed out"),
    ), patch(
        "app.integrations.order_pickup_client.get_order_invoice_source",
        side_effect=OrderPickupClientError("503"),
    ), patch(
        "app.integrations.order_pickup_client.get_order_snapshot",
        return_value=status_wrap,
    ):
        out = get_order_snapshot_for_invoice("ord_1")
    assert out["contract_version"] == 2


def test_404_fiscal_uses_status():
    status_wrap = {"ok": True, **_v2_payload("ord_x")}
    with patch(
        "app.integrations.order_pickup_client.get_order_fiscal_context",
        side_effect=OrderPickupClientError("status=404 detail=order not found"),
    ), patch(
        "app.integrations.order_pickup_client.get_order_invoice_source",
    ) as inv, patch(
        "app.integrations.order_pickup_client.get_order_snapshot",
        return_value=status_wrap,
    ):
        out = get_order_snapshot_for_invoice("ord_x")
    inv.assert_not_called()
    assert out["order"]["id"] == "ord_x"


def test_fiscal_no_contract_falls_back_to_status():
    with patch(
        "app.integrations.order_pickup_client.get_order_fiscal_context",
        return_value={"ok": True, "order": {"id": "1"}},
    ), patch(
        "app.integrations.order_pickup_client.get_order_snapshot",
        return_value={"ok": True, **_v2_payload("1")},
    ):
        out = get_order_snapshot_for_invoice("1")
    assert out["contract_version"] == 2
