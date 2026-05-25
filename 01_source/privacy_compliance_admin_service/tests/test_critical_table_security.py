from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"
CONSENTS_API = f"{API}/consents"


def test_consents_denied_usuario_comum_list(client):
    r = client.get(CONSENTS_API, headers={"X-Actor-Roles": "usuario_comum"})
    assert r.status_code == 403


def test_consents_allowed_admin(client):
    client.post(f"{API}/seed")
    r = client.get(CONSENTS_API, headers={"X-Actor-Roles": "admin_operacao"})
    assert r.status_code == 200
