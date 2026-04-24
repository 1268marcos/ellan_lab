def test_callback_payload_shape_guard():
    payload = {
        "invoice_id": "inv_1",
        "authority": "SEFAZ",
        "event_type": "AUTH_RESULT",
        "status": "AUTHORIZED",
        "protocol_number": "P123",
        "raw": {"x": 1},
    }
    assert payload["authority"] in {"SEFAZ", "AT", "AEAT"}
    assert isinstance(payload["invoice_id"], str) and payload["invoice_id"]
