from app.services import sefaz_svrs_batch_stub_service as svc


def test_svrs_batch_submit_and_query_processing_then_processed():
    svc.reset_svrs_issue_batch_stub_state()
    submit = svc.submit_svrs_issue_batch_stub(
        {
            "invoice_id": "inv_1",
            "order_id": "ord_1",
            "idempotency_key": "k-1",
            "ready_after_polls": 2,
        }
    )
    assert submit["batch_status"] == "RECEIVED"
    receipt = submit["receipt_number"]

    q1 = svc.query_svrs_issue_batch_stub(receipt)
    assert q1["batch_status"] == "PROCESSING"

    q2 = svc.query_svrs_issue_batch_stub(receipt)
    assert q2["batch_status"] == "PROCESSED"
    assert q2["result"]["provider_status"] == "AUTHORIZED"


def test_svrs_batch_idempotency_reuses_receipt():
    svc.reset_svrs_issue_batch_stub_state()
    first = svc.submit_svrs_issue_batch_stub({"idempotency_key": "same-key", "invoice_id": "inv_2"})
    second = svc.submit_svrs_issue_batch_stub({"idempotency_key": "same-key", "invoice_id": "inv_2"})
    assert first["receipt_number"] == second["receipt_number"]
    assert second["idempotent_replay"] is True
