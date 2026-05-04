from __future__ import annotations

from datetime import datetime, timezone
from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import feature_flags
from app.core.config import settings
from app.core.db import Base
from app.models.products_cache import ProductsCache, _utcnow
from app.services import (
    catalog_client,
    catalog_sync_service,
    inventory_client,
    partner_client,
    rollback_service,
    v1_order_bridge,
    v1_payment_bridge,
    wallet_client,
)


def setup_module() -> None:
    feature_flags.reset_overrides()
    feature_flags.reset_metrics()
    rollback_service.reset_window()


def teardown_function() -> None:
    feature_flags.reset_overrides()
    feature_flags.reset_metrics()
    rollback_service.reset_window()


def test_feature_flags_snapshot_and_public_dict():
    feature_flags.set_flag_override("USE_CATALOG_SERVICE", True)
    d = feature_flags.as_public_dict()
    assert d["USE_CATALOG_SERVICE"] is True
    feature_flags.set_flag_override("USE_CATALOG_SERVICE", None)


def test_apply_rollback_all_off():
    feature_flags.set_flag_override("USE_CATALOG_SERVICE", True)
    feature_flags.apply_rollback_all_off()
    assert feature_flags.use_catalog_service() is False


def test_metrics_record():
    feature_flags.reset_metrics()
    feature_flags.record_http_outcome(status_code=200)
    feature_flags.record_http_outcome(status_code=500)
    m = feature_flags.get_metrics()
    assert m["total_requests"] == 2
    assert m["error_responses"] == 1


def test_rollback_trigger(monkeypatch):
    monkeypatch.setattr(settings, "rollback_min_samples", 2)
    monkeypatch.setattr(settings, "rollback_error_rate_threshold", 0.2)
    monkeypatch.setattr(settings, "rollback_window_seconds", 3600)
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", True)
    rollback_service.reset_window()
    rollback_service.observe_request_outcome(is_error=True)
    rollback_service.observe_request_outcome(is_error=True)
    assert rollback_service.should_trigger_rollback() is True
    assert rollback_service.maybe_execute_rollback() is True
    assert feature_flags.use_catalog_service() is False


def test_maybe_execute_rollback_false():
    assert rollback_service.maybe_execute_rollback() is False


def test_should_trigger_auto_disabled():
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", False)
    rollback_service.reset_window()
    rollback_service.observe_request_outcome(is_error=True)
    assert rollback_service.should_trigger_rollback() is False
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", None)


def test_rollback_no_trigger_low_samples(monkeypatch):
    monkeypatch.setattr(settings, "rollback_min_samples", 10)
    rollback_service.reset_window()
    rollback_service.observe_request_outcome(is_error=True)
    assert rollback_service.should_trigger_rollback() is False


def test_rollback_no_trigger_low_samples_auto_on(monkeypatch):
    monkeypatch.setattr(settings, "rollback_min_samples", 10)
    monkeypatch.setattr(settings, "auto_rollback_enabled", True)
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", True)
    rollback_service.reset_window()
    rollback_service.observe_request_outcome(is_error=True)
    assert rollback_service.should_trigger_rollback() is False
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", None)
    monkeypatch.setattr(settings, "auto_rollback_enabled", False)


def test_window_error_rate_empty():
    rollback_service.reset_window()
    assert rollback_service.window_error_rate() == 0.0


def test_rollback_prune_removes_stale_entries(monkeypatch):
    monkeypatch.setattr(settings, "rollback_window_seconds", 30)
    rollback_service.reset_window()
    seq = iter([1000.0, 1050.0])
    monkeypatch.setattr(rollback_service.time, "time", lambda: next(seq))
    rollback_service.observe_request_outcome(is_error=False)
    rollback_service.observe_request_outcome(is_error=False)
    assert len(rollback_service._window) == 1


def test_products_cache_utcnow():
    assert _utcnow().tzinfo is not None


def test_map_catalog_parse_dt_branches():
    dt = datetime(2024, 1, 2, tzinfo=timezone.utc)
    dto = catalog_sync_service.map_catalog_payload_to_dto(
        {
            "order_pickup_cache": {
                "sku_id": "s",
                "name": "N",
                "category_id": "C",
                "amount_cents": 1,
                "created_at": dt,
                "updated_at": "not-a-valid-date",
            }
        }
    )
    assert dto.created_at == dt
    assert dto.updated_at is None


def test_map_catalog_created_at_non_parsable_type():
    dto = catalog_sync_service.map_catalog_payload_to_dto(
        {
            "order_pickup_cache": {
                "sku_id": "s",
                "name": "N",
                "category_id": "C",
                "amount_cents": 1,
                "created_at": 12345,
            }
        }
    )
    assert dto.created_at is None


def test_catalog_client_fetch_json(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"sku_id": "1", "order_pickup_cache": {"sku_id": "1"}}

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url: str):
            return _Resp()

    monkeypatch.setattr(settings, "catalog_service_base_url", "http://cat.test")
    monkeypatch.setattr(catalog_client.httpx, "Client", lambda **kw: _Client())
    out = catalog_client.fetch_product_json(sku_id="abc")
    assert out["sku_id"] == "1"


def test_catalog_client_safe_none(monkeypatch):
    monkeypatch.setattr(settings, "catalog_service_base_url", "http://invalid.local")
    assert catalog_client.fetch_product_safe(sku_id="x") is None


def test_partner_client_safe(monkeypatch):
    monkeypatch.setattr(settings, "partner_service_base_url", "http://invalid.local")
    assert partner_client.fetch_partner_safe(partner_id="p") is None


def test_partner_client_json(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"id": "p1"}

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url: str):
            return _Resp()

    monkeypatch.setattr(settings, "partner_service_base_url", "http://p.test")
    monkeypatch.setattr(partner_client.httpx, "Client", lambda **kw: _Client())
    assert partner_client.fetch_partner_json(partner_id="p1")["id"] == "p1"


def test_partner_client_invalid_type(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return []

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url: str):
            return _Resp()

    monkeypatch.setattr(settings, "partner_service_base_url", "http://p.test")
    monkeypatch.setattr(partner_client.httpx, "Client", lambda **kw: _Client())
    with pytest.raises(ValueError):
        partner_client.fetch_partner_json(partner_id="p1")


def test_inventory_hook_non_dict_json(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return "x"

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, json=None):
            return _Resp()

    monkeypatch.setattr(settings, "inventory_service_base_url", "http://inv.test")
    monkeypatch.setattr(inventory_client.httpx, "Client", lambda **kw: _Client())
    assert inventory_client.post_inventory_hook(order_id="o") == {"raw": "x"}


def test_inventory_hook_json(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"ok": True}

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, json=None):
            return _Resp()

    monkeypatch.setattr(settings, "inventory_service_base_url", "http://inv.test")
    monkeypatch.setattr(inventory_client.httpx, "Client", lambda **kw: _Client())
    assert inventory_client.post_inventory_hook(order_id="o")["ok"] is True


def test_wallet_hook_json(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"ok": True}

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, json=None):
            return _Resp()

    monkeypatch.setattr(settings, "wallet_service_base_url", "http://w.test")
    monkeypatch.setattr(wallet_client.httpx, "Client", lambda **kw: _Client())
    assert wallet_client.post_wallet_hook(order_id="o")["ok"] is True


def test_inventory_wallet_safe(monkeypatch):
    monkeypatch.setattr(settings, "inventory_service_base_url", "http://invalid.local")
    monkeypatch.setattr(settings, "wallet_service_base_url", "http://invalid.local")
    assert inventory_client.post_inventory_hook_safe(order_id="o") is None
    assert wallet_client.post_wallet_hook_safe(order_id="o") is None


def test_catalog_sync_map_and_upsert():
    eng = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=eng)
    Base.metadata.create_all(eng, tables=[ProductsCache.__table__])
    db = Session()
    try:
        payload = {
            "order_pickup_cache": {
                "sku_id": "s1",
                "partner_id": "p",
                "partner_sku": "ps",
                "name": "N",
                "description": None,
                "category_id": "CAT",
                "amount_cents": 10,
                "currency": "BRL",
                "width_mm": 1,
                "height_mm": 2,
                "depth_mm": 3,
                "weight_g": 4,
                "is_active": True,
                "requires_signature": False,
                "is_hazardous": False,
                "temperature_zone": "AMBIENT",
            }
        }
        dto = catalog_sync_service.map_catalog_payload_to_dto(payload)
        assert dto.sku_id == "s1"
        catalog_sync_service.upsert_products_cache_from_catalog(db, payload)
        row = db.query(ProductsCache).one()
        assert row.name == "N"
        payload["order_pickup_cache"]["name"] = "N2"
        catalog_sync_service.upsert_products_cache_from_catalog(db, payload)
        row2 = db.query(ProductsCache).filter(ProductsCache.sku_id == "s1").one()
        assert row2.name == "N2"
        catalog_sync_service.apply_stream_event_payload(db, "product.deprecated", dict(payload["order_pickup_cache"]))
        catalog_sync_service.apply_stream_event_payload(db, "product.unknown", {})
    finally:
        db.close()


def test_apply_stream_known():
    eng = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=eng)
    Base.metadata.create_all(eng, tables=[ProductsCache.__table__])
    db = Session()
    try:
        catalog_sync_service.apply_stream_event_payload(
            db,
            "product.price_changed",
            {
                "order_pickup_cache": {
                    "sku_id": "z",
                    "name": "Z",
                    "category_id": "C",
                    "amount_cents": 1,
                    "currency": "BRL",
                }
            },
        )
    finally:
        db.close()


def test_map_catalog_invalid_dates():
    dto = catalog_sync_service.map_catalog_payload_to_dto(
        {
            "sku_id": "t",
            "name": "N",
            "category_id": "C",
            "amount_cents": 5,
            "currency": "BRL",
            "created_at": "not-a-date",
            "updated_at": "also-bad",
        }
    )
    assert dto.created_at is None and dto.updated_at is None


def test_map_catalog_top_level_only():
    dto = catalog_sync_service.map_catalog_payload_to_dto(
        {"sku_id": "t", "name": "N", "category_id": "C", "amount_cents": 5, "currency": "BRL"}
    )
    assert dto.sku_id == "t"


def test_catalog_client_invalid_json_type(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return []

    class _Client:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url: str):
            return _Resp()

    monkeypatch.setattr(settings, "catalog_service_base_url", "http://cat.test")
    monkeypatch.setattr(catalog_client.httpx, "Client", lambda **kw: _Client())
    with pytest.raises(ValueError):
        catalog_client.fetch_product_json(sku_id="x")


def test_v1_payment_bridge(monkeypatch):
    calls: list[str] = []

    def w(*args, **kwargs):
        calls.append("w")

    def i(*args, **kwargs):
        calls.append("i")

    monkeypatch.setattr(feature_flags, "use_wallet_service", lambda: True)
    monkeypatch.setattr(feature_flags, "use_inventory_service", lambda: True)
    monkeypatch.setattr(wallet_client, "post_wallet_hook_safe", w)
    monkeypatch.setattr(inventory_client, "post_inventory_hook_safe", i)
    v1_payment_bridge.post_confirm_side_effects("ord")
    assert calls == ["w", "i"]


def test_maybe_validate_partner(monkeypatch):
    monkeypatch.setattr(feature_flags, "use_partner_service", lambda: True)
    monkeypatch.setattr(partner_client, "fetch_partner_json", lambda partner_id: {"id": partner_id})
    v1_order_bridge.maybe_validate_partner("pid")


def test_maybe_validate_catalog_and_shadow(monkeypatch):
    monkeypatch.setattr(feature_flags, "use_catalog_service", lambda: False)
    monkeypatch.setattr(feature_flags, "shadow_mode_enabled", lambda: True)
    monkeypatch.setattr(catalog_client, "fetch_product_safe", lambda sku_id: {"order_pickup_cache": {"sku_id": sku_id, "amount_cents": 1, "category_id": "C", "name": "N"}})
    v1_order_bridge.maybe_validate_with_catalog_service("sku")


def test_maybe_validate_catalog_strict(monkeypatch):
    monkeypatch.setattr(feature_flags, "use_catalog_service", lambda: True)
    monkeypatch.setattr(feature_flags, "shadow_mode_enabled", lambda: False)
    monkeypatch.setattr(catalog_client, "fetch_product_json", lambda sku_id: {"sku_id": sku_id})
    v1_order_bridge.maybe_validate_with_catalog_service("sku")


def test_maybe_validate_empty_sku():
    v1_order_bridge.maybe_validate_with_catalog_service(None)
    v1_order_bridge.maybe_validate_partner(None)
