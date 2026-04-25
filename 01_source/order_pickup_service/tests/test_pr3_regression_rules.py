from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.routers.pricing_fiscal import _compute_advanced_discount, validate_promotion
from app.schemas.pricing_fiscal import PromotionValidateIn
from app.services import fiscal_context_service as fcs


def test_compute_advanced_discount_buy_x_get_y():
    discount = _compute_advanced_discount(
        promo_type="BUY_X_GET_Y",
        total_amount_cents=10000,
        discount_pct=None,
        discount_cents=None,
        max_discount_cents=None,
        conditions_json={"buy_qty": 2, "get_qty": 1, "free_item_price_cents": 300},
        items=[{"quantity": 6, "unit_price_cents": 500}],
    )
    assert discount == 600


def test_compute_advanced_discount_free_item():
    discount = _compute_advanced_discount(
        promo_type="FREE_ITEM",
        total_amount_cents=10000,
        discount_pct=None,
        discount_cents=None,
        max_discount_cents=None,
        conditions_json={"free_qty": 2, "free_item_price_cents": 450},
        items=[{"quantity": 2, "unit_price_cents": 700}],
    )
    assert discount == 900


def test_compute_advanced_discount_bundle_discount_with_cap():
    discount = _compute_advanced_discount(
        promo_type="BUNDLE_DISCOUNT",
        total_amount_cents=10000,
        discount_pct=None,
        discount_cents=None,
        max_discount_cents=250,
        conditions_json={"bundle_size": 2, "bundle_price_cents": 500},
        items=[
            {"quantity": 1, "unit_price_cents": 400},
            {"quantity": 1, "unit_price_cents": 300},
        ],
    )
    assert discount == 200


class _FakeResult:
    def __init__(self, row: dict | None):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeIdempotentDb:
    def __init__(self):
        self.commit_calls = 0

    def execute(self, statement, params=None):  # noqa: ANN001
        sql = str(statement)
        if "FROM ops_action_audit" in sql:
            return _FakeResult(
                {
                    "details_json": {
                        "after": {
                            "ok": True,
                            "valid": True,
                            "promotion_id": "promo-1",
                            "promotion_code": "PROMO10",
                            "discount_cents": 123,
                            "reason": None,
                        }
                    }
                }
            )
        raise AssertionError(f"SQL inesperado no teste idempotente: {sql}")

    def commit(self):
        self.commit_calls += 1


def test_validate_promotion_idempotent_hit(monkeypatch):
    db = _FakeIdempotentDb()
    payload = PromotionValidateIn(
        promotion_code="PROMO10",
        order_id="ord-1",
        total_amount_cents=1000,
        items=[],
    )
    monkeypatch.setattr("app.routers.pricing_fiscal._record_pr3_audit", lambda **kwargs: None)
    out = validate_promotion(
        payload=payload,
        correlation_id="corr-test",
        current_user=SimpleNamespace(id="user-1"),
        db=db,
    )
    assert out.idempotent is True
    assert out.valid is True
    assert out.discount_cents == 123
    assert out.promotion_code == "PROMO10"
    assert db.commit_calls == 1


def test_apply_auto_fiscal_classification_category_fallback_and_default(monkeypatch):
    logged_sources: list[tuple[str, str]] = []
    default_alerts: list[tuple[str, str]] = []
    outbox_calls: list[tuple[str, dict]] = []
    outbox_audits: list[str] = []

    monkeypatch.setattr(fcs, "_resolve_fiscal_by_product", lambda db, sku_id: None)

    def _fake_category(db, sku_id):  # noqa: ANN001
        if sku_id == "sku-category":
            return {
                "ncm_code": "11111111",
                "icms_cst": "00",
                "pis_cst": "01",
                "cofins_cst": "01",
                "cfop": "5101",
            }
        return None

    monkeypatch.setattr(fcs, "_resolve_fiscal_by_category", _fake_category)
    monkeypatch.setattr(
        fcs,
        "_resolve_fiscal_defaults",
        lambda: {
            "ncm_code": "00000000",
            "icms_cst": "90",
            "pis_cst": "99",
            "cofins_cst": "99",
            "cfop": "5102",
        },
    )
    monkeypatch.setattr(
        fcs,
        "_insert_fiscal_auto_classification_log",
        lambda db, order_id, invoice_id, sku_id, source, fiscal: logged_sources.append((sku_id, source)),
    )
    monkeypatch.setattr(
        fcs,
        "_record_default_fiscal_alert",
        lambda db, order_id, sku_id: default_alerts.append((order_id, sku_id)),
    )
    monkeypatch.setattr(
        fcs,
        "enqueue_partner_order_paid_event_if_needed",
        lambda db, order_id, payload: (
            outbox_calls.append((order_id, payload)) or ({"id": "out-1", "partner_id": "ptn_fiscal_stub"}, False)
        ),
    )
    monkeypatch.setattr(
        fcs,
        "record_ops_action_audit",
        lambda **kwargs: outbox_audits.append(str(kwargs.get("action"))),
    )

    items = [
        {"sku_id": "sku-category", "quantity": 1, "unit_price_cents": 1000},
        {"sku_id": "sku-default", "quantity": 1, "unit_price_cents": 900},
    ]
    out = fcs._apply_auto_fiscal_classification(
        db=object(),
        order=SimpleNamespace(id="ord-1"),
        items=items,
    )

    assert len(out) == 2
    assert out[0]["fiscal_classification"]["source"] == "CATEGORY_FALLBACK"
    assert out[1]["fiscal_classification"]["source"] == "DEFAULT"
    assert ("sku-category", "CATEGORY_FALLBACK") in logged_sources
    assert ("sku-default", "DEFAULT") in logged_sources
    assert default_alerts == [("ord-1", "sku-default")]
    assert len(outbox_calls) == 1
    assert "I1_ORDER_FISCAL_OUTBOX_ENQUEUE" in outbox_audits

