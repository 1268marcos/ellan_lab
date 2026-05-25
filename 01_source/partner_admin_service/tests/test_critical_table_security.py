from __future__ import annotations

USERS_API = "/api/v1/partner-admin/users"
AUDIT_API = "/api/v1/partner-admin/critical-audit-logs"


def test_users_denied_without_role(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.get(USERS_API, headers={"X-Actor-Roles": "usuario_comum"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "critical_table_denied"


def test_users_allowed_admin_operacao(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.get(USERS_API, headers={"X-Actor-Roles": "admin_operacao"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_users_self_scope(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.get(
        f"{USERS_API}/usr-admin-ops",
        headers={"X-Actor-Id": "usr-admin-ops", "X-Actor-Roles": "usuario_comum"},
    )
    assert r.status_code == 200


def test_audit_logs_list_requires_auditoria(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.get(AUDIT_API, headers={"X-Actor-Roles": "suporte"})
    assert r.status_code == 403
