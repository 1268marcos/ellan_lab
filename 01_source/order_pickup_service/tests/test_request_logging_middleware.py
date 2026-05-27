from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.structured_logging import configure_structured_logging
from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    extract_order_id_from_path,
    is_critical_path,
    resolve_correlation_id,
)


def test_extract_order_id_from_path():
    assert extract_order_id_from_path("/public/orders/ord-123/cancel") == "ord-123"
    assert extract_order_id_from_path("/orders/") is None
    assert extract_order_id_from_path("/health") is None


def test_is_critical_path():
    assert is_critical_path("/public/orders/abc")
    assert is_critical_path("/totem/pickups/redeem-manual")
    assert not is_critical_path("/health")


def test_request_logging_middleware_sets_correlation_header():
    configure_structured_logging(log_level="WARNING")
    app = FastAPI()

    @app.get("/public/orders/{order_id}")
    def sample(order_id: str):
        return {"order_id": order_id}

    app.add_middleware(RequestLoggingMiddleware)

    client = TestClient(app)
    response = client.get(
        "/public/orders/order-xyz",
        headers={"X-Correlation-Id": "corr-test-001"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr-test-001"
    assert response.headers.get("X-Trace-Id") == "corr-test-001"


def test_resolve_correlation_id_generates_uuid_when_missing():
    class _Req:
        headers = {}

    corr = resolve_correlation_id(_Req())  # type: ignore[arg-type]
    assert len(corr) >= 32
