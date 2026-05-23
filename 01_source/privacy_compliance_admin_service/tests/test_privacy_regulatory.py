from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_regulatory_toolkit_and_rights(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/regulatory/toolkit?regulation_code=GDPR")
    assert r.status_code == 200
    toolkit = r.json()
    assert toolkit["regulation_code"] == "GDPR"
    assert toolkit["summary"]["subject_rights_count"] >= 6
    assert toolkit["summary"]["obligations_count"] >= 5
    assert len(toolkit["subject_rights"]) >= 6
    assert len(toolkit["authority_templates"]) >= 1
    assert toolkit["authority_templates"][0]["deadline_hours"] == 72

    r = client.get(f"{API}/regulatory/toolkit?regulation_code=LGPD")
    assert r.status_code == 200
    lgpd = r.json()
    assert lgpd["summary"]["subject_rights_count"] >= 7

    r = client.get(f"{API}/regulatory/toolkit?regulation_code=CCPA")
    assert r.status_code == 200
    ccpa = r.json()
    assert ccpa["summary"]["opt_out_count"] >= 1
    assert any(o["obligation_code"] == "GPC_HONORED" for o in ccpa["obligations"])


def test_subject_rights_compare(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/regulatory/compare-rights?codes=GDPR,LGPD,CCPA")
    assert r.status_code == 200
    cmp = r.json()
    assert len(cmp["codes"]) == 3
    assert "GDPR" in cmp["rights_by_code"]
    assert len(cmp["common_dsar_types"]) >= 3


def test_obligations_lia_opt_out(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/regulatory/obligations?regulation_code=GDPR")
    assert r.status_code == 200
    obligations = r.json()
    assert obligations["total"] >= 5
    obl_id = obligations["items"][0]["id"]

    r = client.patch(f"{API}/regulatory/obligations/{obl_id}", json={"compliance_status": "COMPLIANT"})
    assert r.status_code == 200
    assert r.json()["compliance_status"] == "COMPLIANT"

    r = client.post(
        f"{API}/regulatory/lia-records",
        json={
            "regulation_code": "GDPR",
            "title": "Test LIA locker analytics",
            "purpose": "Aggregate locker usage metrics without PII",
            "status": "DRAFT",
        },
    )
    assert r.status_code == 201
    assert r.json()["regulation_code"] == "GDPR"

    r = client.post(
        f"{API}/regulatory/opt-out-records",
        json={
            "regulation_code": "CCPA",
            "user_id": "usr-test-001",
            "opt_out_type": "SALE_SHARE",
            "signal_source": "GPC",
            "gpc_signal": True,
        },
    )
    assert r.status_code == 201
    assert r.json()["gpc_signal"] is True


def test_compliance_score_includes_regulatory(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/compliance/score?regulation_code=GDPR&persist=false")
    assert r.status_code == 200
    score = r.json()
    keys = {d["key"] for d in score["dimensions"]}
    assert "regulatory" in keys
