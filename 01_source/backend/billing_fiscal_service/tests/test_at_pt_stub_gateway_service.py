from __future__ import annotations

import pytest

from app.services import at_pt_stub_gateway_service as gw


@pytest.fixture(autouse=True)
def _reset_gateway():
    gw.reset_at_pt_stub_gateway_state()
    yield
    gw.reset_at_pt_stub_gateway_state()


def test_issue_rest_envelope_and_provider_shape():
    out = gw.submit_at_pt_stub_issue(
        {"order_id": "ord-1", "invoice_id": "inv-1", "amount_cents": 1234, "currency": "EUR"},
        wire_mode="rest",
    )
    assert "provider_result" in out
    assert out["wire_mode"] == "rest"
    assert out["wire_envelope"]["transport"] == "http_json"
    assert out["idempotent_replay"] is False
    pr = out["provider_result"]
    assert pr["invoice_number"]
    assert pr["access_key"]
    assert pr["government_response"]["provider_code"] == "AT-200"


def test_issue_soap_envelope():
    out = gw.submit_at_pt_stub_issue(
        {"idempotency_key": "k-soap-1", "order_id": "o", "amount_cents": 100},
        wire_mode="soap",
    )
    assert out["wire_mode"] == "soap"
    env = out["wire_envelope"]
    assert env["transport"] == "soap12"
    assert "soap_action" in env
    assert "PayloadB64" in env["body_xml_preview"]


def test_issue_idempotency_replay():
    p = {"idempotency_key": "idem-xyz", "order_id": "o1", "invoice_id": "i1"}
    first = gw.submit_at_pt_stub_issue(p, wire_mode="rest")
    second = gw.submit_at_pt_stub_issue(p, wire_mode="rest")
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["provider_result"]["access_key"] == first["provider_result"]["access_key"]


def test_issue_requires_ids_or_idempotency():
    with pytest.raises(ValueError, match="idempotency"):
        gw.submit_at_pt_stub_issue({"amount_cents": 1})


def test_cancel_requires_context():
    with pytest.raises(ValueError, match="cancel_requires"):
        gw.submit_at_pt_stub_cancel({})


def test_cancel_ok():
    out = gw.submit_at_pt_stub_cancel({"access_key": "at_manual_key_1", "order_id": "o9"}, wire_mode="rest")
    assert out["operation"] == "CANCEL"
    assert out["provider_result"]["cancel_status"] == "CANCELLED"
