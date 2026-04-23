from __future__ import annotations

from app.models.invoice_model import Invoice
from app.services.tax_service import build_tax_breakdown


def _inv(**kwargs) -> Invoice:
    inv = Invoice()
    for k, v in kwargs.items():
        setattr(inv, k, v)
    return inv


def test_br_sp_icms_and_pis_cofins():
    inv = _inv(
        country="BR",
        region="SP",
        amount_cents=10_000,
        order_snapshot={"order": {"sku_id": "SKU1"}, "tenant_fiscal": {"regime": "LUCRO_PRESUMIDO"}},
        items_json={"lines": [{"sku_id": "SKU1", "quantity": 1, "total_amount_cents": 10_000}]},
    )
    out = build_tax_breakdown(None, inv)
    line = out["lines"][0]
    assert line["icms_rate"] == 0.18
    assert line["icms_cents"] == 1800
    assert line["pis_cents"] == 65
    assert line["cofins_cents"] == 300


def test_br_rj_icms():
    inv = _inv(
        country="BR",
        region="RJ",
        amount_cents=1000,
        order_snapshot={"order": {"sku_id": "X"}, "tenant_fiscal": {"regime": "LUCRO_REAL"}},
        items_json={"lines": [{"sku_id": "X", "quantity": 1, "total_amount_cents": 1000}]},
    )
    out = build_tax_breakdown(None, inv)
    assert out["lines"][0]["icms_rate"] == 0.20


def test_br_simples_zero_icms():
    inv = _inv(
        country="BR",
        region="SP",
        amount_cents=5000,
        order_snapshot={"order": {"sku_id": "S"}, "tenant_fiscal": {"regime": "SIMPLES"}},
        items_json={"lines": [{"sku_id": "S", "quantity": 1, "total_amount_cents": 5000}]},
    )
    out = build_tax_breakdown(None, inv)
    line = out["lines"][0]
    assert line["icms_cents"] == 0
    assert line["pis_cents"] > 0


def test_pt_iva_normal():
    inv = _inv(
        country="PT",
        region="PT",
        amount_cents=1000,
        order_snapshot={"order": {"sku_id": "P1"}},
        items_json={"lines": [{"sku_id": "P1", "quantity": 1, "total_amount_cents": 1000}]},
    )
    out = build_tax_breakdown(None, inv)
    assert out["lines"][0]["iva_rate"] == 0.23
    assert out["lines"][0]["iva_cents"] == 230


def test_pt_iva_reduzida_from_product_config_memory():
    """Sem DB: categoria vem só se houver ProductFiscalConfig — aqui valida default NORMAL."""
    inv = _inv(
        country="PT",
        region="PT",
        amount_cents=100,
        order_snapshot={"order": {"sku_id": "unknown"}},
        items_json={"lines": [{"sku_id": "unknown", "quantity": 1, "total_amount_cents": 100}]},
    )
    out = build_tax_breakdown(None, inv)
    assert out["lines"][0]["iva_category"] == "NORMAL"
