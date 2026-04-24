from app.services.fiscal_reconciliation_service import _build_gap_candidates


def test_build_gap_candidates_types_and_keys():
    rows = _build_gap_candidates(
        paid_without_invoice=["ord_1", "ord_2"],
        issued_without_paid=[("ord_9", "inv_9")],
    )
    keys = {r.dedupe_key for r in rows}
    assert "paid_without_invoice:ord_1" in keys
    assert "paid_without_invoice:ord_2" in keys
    assert "issued_without_paid:inv_9" in keys
    assert len(rows) == 3


def test_build_gap_candidates_sets_severity_error():
    rows = _build_gap_candidates(
        paid_without_invoice=["ord_x"],
        issued_without_paid=[("ord_y", "inv_y")],
    )
    assert all(r.severity == "ERROR" for r in rows)
