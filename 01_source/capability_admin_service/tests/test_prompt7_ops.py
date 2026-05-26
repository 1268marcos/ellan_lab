from __future__ import annotations

PREFIX = "/api/v1/capability-admin"


def test_resolve_and_simulate(client):
    client.post(f"{PREFIX}/seed")
    profiles = client.get(f"{PREFIX}/profiles").json()["items"]
    pid = profiles[0]["id"]
    resolved = client.post(
        f"{PREFIX}/ops/resolve",
        json={"region_code": "SP", "channel_code": "kiosk", "context_code": "purchase"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["profile_code"] == "SP:kiosk:purchase"

    sim = client.post(f"{PREFIX}/ops/profiles/{pid}/simulate", params={"flow": "pay"})
    assert sim.status_code == 200
    assert "allowed" in sim.json()


def test_clone_compare_export_templates(client):
    client.post(f"{PREFIX}/seed")
    profiles = client.get(f"{PREFIX}/profiles").json()["items"]
    src = profiles[0]
    pid_b = profiles[1]["id"] if len(profiles) > 1 else src["id"]

    regions = {r["code"]: r for r in client.get(f"{PREFIX}/regions").json()["items"]}
    channels = {c["code"]: c for c in client.get(f"{PREFIX}/channels").json()["items"]}
    contexts = client.get(f"{PREFIX}/contexts").json()["items"]
    partner_ctx = next(
        c for c in contexts if c["code"] == "webhook_payment" and channels.get("partner", {}).get("id") == c.get("channel_id")
    )
    if not partner_ctx:
        partner_ctx = contexts[0]
    clone = client.post(
        f"{PREFIX}/ops/profiles/clone",
        json={
            "source_profile_id": src["id"],
            "profile_code": "SP:partner:webhook_payment",
            "name": "Clone SP Partner",
            "region_id": regions["SP"]["id"],
            "channel_id": channels["partner"]["id"],
            "context_id": partner_ctx["id"],
            "copy_bindings": False,
        },
    )
    assert clone.status_code == 201

    cmp = client.get(
        f"{PREFIX}/ops/profiles/compare",
        params={"profile_id_a": src["id"], "profile_id_b": pid_b},
    )
    assert cmp.status_code == 200

    exp = client.get(f"{PREFIX}/ops/profiles/{src['id']}/export")
    assert exp.status_code == 200
    assert exp.json()["version"] == 1

    tpl = client.get(f"{PREFIX}/ops/templates")
    assert tpl.status_code == 200
    assert tpl.json()["total"] >= 1

    jobs = client.get(f"{PREFIX}/ops/jobs")
    assert jobs.status_code == 200
    assert jobs.json()["total"] >= 1
