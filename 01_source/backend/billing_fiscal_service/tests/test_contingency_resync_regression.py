"""
F3C-STUB-04 — regressão contingência BR (OFFLINE_SAT / CONTINGENCY_SVRS) + re-sync (`sync_pending`).

Garante: stub de contingência marca `sync_pending`; `route_issue_invoice_reconnect` não reentra em contingência;
`claim_and_process_resync_invoice_by_id` limpa `sync_pending` quando o stub SEFAZ-SP responde (BD real).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

import app.core.config as cfg
from sqlalchemy import text

from app.core.db import SessionLocal
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_issue_invoice, route_issue_invoice_reconnect
from app.services.invoice_resync_service import claim_and_process_resync_invoice_by_id, list_eligible_resync_invoice_ids
from app.services.sefaz_contingency_service import issue_invoice_contingency_stub


@pytest.mark.parametrize(
    "mode,expected_series",
    [
        ("OFFLINE_SAT", "SAT-1"),
        ("CONTINGENCY_SVRS", "SVRS-CONT-1"),
    ],
)
def test_contingency_stub_sets_sync_pending(mode, expected_series):
    inv = Invoice(
        id=f"ctg-{uuid4().hex[:10]}",
        order_id=f"ord-{uuid4().hex[:10]}",
        country="BR",
        emission_mode=mode,
        fiscal_doc_subtype="NFC_E_65",
        amount_cents=100,
        currency="BRL",
    )
    out = issue_invoice_contingency_stub(inv)
    assert out["status"] == "ISSUED"
    assert out["invoice_series"] == expected_series
    gov = out["government_response"]
    assert gov.get("sync_pending") is True
    assert gov.get("provider_status") == "CONTINGENCY_PENDING_SYNC"
    assert out["xml_content"]["emission_mode"] == mode


def test_route_issue_invoice_br_contingency_not_normal_stub(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_br_enabled", False)
    inv = Invoice(
        id=f"r-{uuid4().hex[:10]}",
        order_id=f"o-{uuid4().hex[:10]}",
        country="BR",
        emission_mode="OFFLINE_SAT",
        fiscal_doc_subtype="NFC_E_65",
    )
    out = route_issue_invoice(inv)
    assert out["government_response"]["provider_status"] == "CONTINGENCY_PENDING_SYNC"


def test_route_issue_invoice_reconnect_br_uses_normal_stub_not_contingency(monkeypatch):
    """Re-sync não deve voltar ao stub de contingência (deve tentar fluxo `sefaz_sp_issue_invoice` quando real off)."""
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_br_enabled", False)
    inv = Invoice(
        id=f"rc-{uuid4().hex[:10]}",
        order_id=f"orc-{uuid4().hex[:10]}",
        country="BR",
        emission_mode="OFFLINE_SAT",
        fiscal_doc_subtype="NFC_E_65",
        amount_cents=200,
        currency="BRL",
        payment_method="PIX",
        emitter_cnpj="12345678000199",
        consumer_cpf="12345678909",
        consumer_name="Cliente",
        order_snapshot={"order": {"sku_id": "x", "receipt_email": "a@b.co"}},
    )
    out = route_issue_invoice_reconnect(inv)
    assert out["government_response"]["provider_status"] != "CONTINGENCY_PENDING_SYNC"
    assert out["government_response"].get("provider_namespace") == "sefaz_sp_stub"


def test_resync_db_clears_sync_pending_after_reconnect(monkeypatch):
    """Exige PostgreSQL (docker compose / CI); em ambiente sem BD faz skip explícito.

    No host, use ``ELL_USE_LOCAL_DOCKER_PG=1`` para ``127.0.0.1:5435`` (ver ``tests/conftest.py``).
    """
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_br_enabled", False)
    iid = f"inv-rsync-{uuid4().hex[:12]}"
    oid = f"ord-rsync-{uuid4().hex[:12]}"
    db = SessionLocal()
    try:
        try:
            db.execute(text("SELECT 1"))
            db.commit()
        except Exception as exc:
            pytest.skip(f"PostgreSQL indisponível neste ambiente: {exc}")

        # issued_at antigo: list_eligible_resync_invoice_ids ordena ASC e limita batch;
        # com now() a linha ficaria atrás de milhares de invoices reais e nunca entraria no lote.
        old_issued = datetime(1970, 1, 2, tzinfo=timezone.utc)
        inv = Invoice(
            id=iid,
            order_id=oid,
            country="BR",
            region="SP",
            emission_mode="OFFLINE_SAT",
            fiscal_doc_subtype="NFC_E_65",
            status=InvoiceStatus.ISSUED,
            amount_cents=300,
            currency="BRL",
            payment_method="PIX",
            issued_at=old_issued,
            emitter_cnpj="12345678000199",
            consumer_cpf="12345678909",
            consumer_name="Cliente RS",
            order_snapshot={"order": {"sku_id": "sku", "receipt_email": "rs@example.com"}},
            government_response={
                "sync_pending": True,
                "sync_id": "sync_test_1",
                "provider_namespace": "sefaz_contingency",
                "provider_status": "CONTINGENCY_PENDING_SYNC",
            },
            invoice_number="CTG1",
            invoice_series="SAT-1",
            access_key="cont_test_key_001",
        )
        db.add(inv)
        db.commit()

        eligible = list_eligible_resync_invoice_ids(db, batch_size=100)
        assert iid in eligible

        processed = claim_and_process_resync_invoice_by_id(db, invoice_id=iid, worker_id="pytest-f3c-stub-04")
        assert processed is not None
        db.refresh(processed)
        assert processed.government_response.get("sync_pending") is False
        assert processed.government_response.get("sync_state") == "SYNCED"
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        try:
            db.query(Invoice).filter(Invoice.id == iid).delete()
            db.commit()
        except Exception:
            db.rollback()
        db.close()
