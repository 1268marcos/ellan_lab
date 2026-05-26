from __future__ import annotations

PREFIX = "/api/v1/capability-admin"


def test_ecosystem_and_matrix(client):
    client.post(f"{PREFIX}/seed")
    seg = client.get(f"{PREFIX}/ecosystem/segments")
    assert seg.status_code == 200
    assert seg.json()["total"] >= 6
    players = client.get(f"{PREFIX}/ecosystem/players", params={"segment_code": "MARKETPLACE"})
    assert players.status_code == 200
    assert players.json()["total"] >= 2
    matrix = client.get(f"{PREFIX}/matrix")
    assert matrix.status_code == 200
    body = matrix.json()
    assert "coverage_pct" in body
    assert len(body["cells"]) > 0


def test_profile_composition(client):
    client.post(f"{PREFIX}/seed")
    profiles = client.get(f"{PREFIX}/profiles").json()["items"]
    pid = profiles[0]["id"]
    actions = client.get(f"{PREFIX}/profiles/{pid}/actions")
    assert actions.status_code == 200
    methods = client.get(f"{PREFIX}/profiles/{pid}/methods")
    assert methods.status_code == 200
    constraints = client.get(f"{PREFIX}/profiles/{pid}/constraints")
    assert constraints.status_code == 200
    new_action = client.post(
        f"{PREFIX}/profiles/{pid}/actions",
        json={"action_code": "refund", "label": "Estorno"},
    )
    assert new_action.status_code == 201


def test_bindings_and_audit(client):
    client.post(f"{PREFIX}/seed")
    bindings = client.get(f"{PREFIX}/ecosystem/bindings")
    assert bindings.status_code == 200
    assert bindings.json()["total"] >= 1
    audit = client.get(f"{PREFIX}/ecosystem/audit-log")
    assert audit.status_code == 200
    dash = client.get(f"{PREFIX}/dashboard")
    d = dash.json()
    assert d["ecosystem_players"] >= 45
    assert d["matrix_coverage_pct"] >= 0
