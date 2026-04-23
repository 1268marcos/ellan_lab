from __future__ import annotations

from app.services.invoice_snapshot_fiscal import (
    EMISSION_MODE_ONLINE,
    FISCAL_DOC_SUBTYPE_NFC_E_65,
    FISCAL_DOC_SUBTYPE_SAFT_PT,
    fiscal_columns_from_order_snapshot,
)


def test_br_defaults_nfc_e_65_and_online():
    snap = {
        "order": {"region": "SP", "totem_id": "TOT-1"},
        "pickup": {"locker_id": "LK-99", "slot": 3},
        "tenant_fiscal": {"cnpj": "12.345.678/0001-90", "razao_social": "ACME LTDA"},
        "consumer_cpf": "12345678909",
        "consumer_name": "Fulano",
        "locker_address": {"city": "São Paulo", "state": "SP"},
        "order_items": [{"sku_id": "SKU1", "quantity": 1}],
    }
    out = fiscal_columns_from_order_snapshot(snap, country="BR")
    assert out["fiscal_doc_subtype"] == FISCAL_DOC_SUBTYPE_NFC_E_65
    assert out["emission_mode"] == EMISSION_MODE_ONLINE
    assert out["locker_id"] == "LK-99"
    assert out["totem_id"] == "TOT-1"
    assert out["slot_label"] == "3"
    assert out["emitter_cnpj"] == "12.345.678/0001-90"
    assert out["emitter_name"] == "ACME LTDA"
    assert out["consumer_cpf"] == "12345678909"
    assert out["consumer_name"] == "Fulano"
    assert out["locker_address"] == {"city": "São Paulo", "state": "SP"}
    assert out["items_json"]["lines"] == [{"sku_id": "SKU1", "quantity": 1}]


def test_pt_saft_subtype():
    snap = {"order": {"region": "PT", "totem_id": "T1"}}
    out = fiscal_columns_from_order_snapshot(snap, country="PT")
    assert out["fiscal_doc_subtype"] == FISCAL_DOC_SUBTYPE_SAFT_PT


def test_locker_id_from_allocation_fallback():
    snap = {
        "order": {"region": "RJ", "totem_id": "X"},
        "allocation": {"locker_id": "AL-1"},
        "pickup": {},
    }
    out = fiscal_columns_from_order_snapshot(snap, country="BR")
    assert out["locker_id"] == "AL-1"


def test_tenant_cnpj_top_level_fallback():
    snap = {
        "order": {"region": "SP", "totem_id": "t"},
        "tenant_cnpj": "11222333000181",
        "tenant_razao_social": "Beta SA",
    }
    out = fiscal_columns_from_order_snapshot(snap, country="BR")
    assert out["emitter_cnpj"] == "11222333000181"
    assert out["emitter_name"] == "Beta SA"


def test_invalid_locker_address_dropped():
    snap = {"order": {"region": "SP", "totem_id": "t"}, "locker_address": "not-a-dict"}
    out = fiscal_columns_from_order_snapshot(snap, country="BR")
    assert out["locker_address"] is None
