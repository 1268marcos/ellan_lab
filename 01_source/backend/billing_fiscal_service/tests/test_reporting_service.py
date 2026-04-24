from datetime import datetime, timezone

from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_reporting_service import (
    build_saft_pt_export_payload,
    build_sped_efd_export_payload,
    month_bounds_utc,
)


def _mk_invoice(i: int, country: str, amount_cents: int) -> Invoice:
    return Invoice(
        id=f"inv_{i}",
        order_id=f"ord_{i}",
        country=country,
        invoice_type="NFE",
        status=InvoiceStatus.ISSUED,
        issued_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
        amount_cents=amount_cents,
        access_key=f"AK{i}",
    )


def test_month_bounds_utc():
    start, end = month_bounds_utc(2026, 12)
    assert start.isoformat().startswith("2026-12-01")
    assert end.isoformat().startswith("2027-01-01")


def test_build_sped_payload_totals():
    payload = build_sped_efd_export_payload(
        year=2026,
        month=4,
        invoices=[_mk_invoice(1, "BR", 100), _mk_invoice(2, "BR", 250)],
    )
    assert payload["format"] == "SPED_EFD_STUB_V1"
    assert payload["invoice_count"] == 2
    assert payload["total_amount_cents"] == 350


def test_build_saft_payload_totals():
    payload = build_saft_pt_export_payload(
        year=2026,
        month=4,
        invoices=[_mk_invoice(1, "PT", 1000)],
    )
    assert payload["format"] == "SAFT_PT_STUB_V1"
    assert payload["invoice_count"] == 1
    assert payload["currency"] == "EUR"
