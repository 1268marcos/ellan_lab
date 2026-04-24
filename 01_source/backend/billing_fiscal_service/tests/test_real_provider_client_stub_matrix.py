from app.integrations import fiscal_real_provider_client as client


def test_stub_matrix_retryable_timeout_exhausts(monkeypatch):
    monkeypatch.setattr(client.settings, "fiscal_real_provider_retries", 1)
    monkeypatch.setattr(client.settings, "fiscal_real_provider_base_url_br", "http://stub.local")
    try:
        client.issue_invoice("BR", {"stub_scenario": "timeout"})
        assert False, "expected RealProviderClientError"
    except client.RealProviderClientError as exc:
        assert exc.code == "PROVIDER_TIMEOUT"
        assert exc.retryable is True
        assert exc.attempts == 2


def test_stub_matrix_non_retryable_validation_stops_first_attempt(monkeypatch):
    monkeypatch.setattr(client.settings, "fiscal_real_provider_retries", 3)
    monkeypatch.setattr(client.settings, "fiscal_real_provider_base_url_br", "http://stub.local")
    try:
        client.issue_invoice("BR", {"stub_scenario": "validation_error"})
        assert False, "expected RealProviderClientError"
    except client.RealProviderClientError as exc:
        assert exc.code == "PROVIDER_VALIDATION_ERROR"
        assert exc.retryable is False
        assert exc.attempts == 1


def test_stub_matrix_recovers_on_success_attempt(monkeypatch):
    monkeypatch.setattr(client.settings, "fiscal_real_provider_retries", 2)
    monkeypatch.setattr(client.settings, "fiscal_real_provider_base_url_br", "http://stub.local")
    out = client.issue_invoice(
        "BR",
        {
            "stub_scenario": "http_5xx",
            "stub_success_on_attempt": 2,
        },
    )
    assert out["provider_status"] == "AUTHORIZED"
    assert out["provider_code"] == "100"


def test_stub_matrix_svrs_batch_async_processing(monkeypatch):
    monkeypatch.setattr(client.settings, "fiscal_real_provider_retries", 2)
    monkeypatch.setattr(client.settings, "fiscal_real_provider_base_url_br", "http://stub.local")
    out = client.issue_invoice(
        "BR",
        {
            "invoice_id": "inv_async_1",
            "order_id": "ord_async_1",
            "stub_scenario": "svrs_batch_async",
            "idempotency_key": "batch-key-1",
            "ready_after_polls": 1,
            "stub_batch_poll_count": 1,
        },
    )
    assert out["batch_async"] is True
    assert out["batch_status"] == "PROCESSED"
    assert out["provider_status"] == "AUTHORIZED"
