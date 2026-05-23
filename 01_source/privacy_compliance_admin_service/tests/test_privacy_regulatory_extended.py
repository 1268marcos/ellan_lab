from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_vcdpa_fadp_au_pa_toolkit(client):
    client.post(f"{API}/seed")

    for code, min_rights in [("VCDPA", 6), ("FADP", 5), ("AU_PA", 4)]:
        r = client.get(f"{API}/regulatory/toolkit?regulation_code={code}")
        assert r.status_code == 200, code
        tk = r.json()
        assert tk["summary"]["subject_rights_count"] >= min_rights


def test_dsar_draft_from_right(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/regulatory/dsar-draft?regulation_code=LGPD&right_code=ACCESS")
    assert r.status_code == 200
    draft = r.json()
    assert draft["request_type"] == "ACCESS"
    assert draft["right_code"] == "ACCESS"
    assert "Solicito acesso" in draft["details"]
    assert draft["subject_line"].startswith("[DSAR/LGPD]")


def test_opt_out_webhook_recorded(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/regulatory/opt-out-records",
        json={
            "regulation_code": "CCPA",
            "user_id": "usr-webhook-test",
            "opt_out_type": "SALE_SHARE",
            "signal_source": "GPC",
            "gpc_signal": True,
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/webhook-deliveries?regulation_code=CCPA&limit=20")
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(d["event_name"] == "opt_out.recorded" for d in items)


def test_player_legal_documents(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/ecosystem/player-legal-documents?limit=100")
    assert r.status_code == 200
    docs = r.json()
    assert docs["total"] >= 55
    assert any(d["player_code"] == "MELI" for d in docs["items"])
    for code in ("RAPPI", "LAZADA", "SF_EXPRESS", "SHEIN", "TEMU", "ALLEGRO", "ZALANDO", "AU_POST"):
        assert any(d["player_code"] == code for d in docs["items"]), f"missing {code}"

    r = client.get(f"{API}/ecosystem/players/RAPPI/legal-documents")
    assert r.status_code == 200
    rappi = r.json()
    assert rappi["player_code"] == "RAPPI"
    assert rappi["items"][0]["public_path"] == "/legal/privacy/player/RAPPI/v1"

    r = client.get(f"{API}/ecosystem/players/MELI/legal-documents")
    assert r.status_code == 200
    meli = r.json()
    assert meli["player_code"] == "MELI"
    assert meli["total"] >= 1
    assert meli["items"][0]["public_path"] == "/legal/privacy/player/MELI/v1"
