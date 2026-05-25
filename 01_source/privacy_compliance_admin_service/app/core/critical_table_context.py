from __future__ import annotations

from fastapi import Header

from shared.security.critical_table_guard import ActorContext


def get_actor_context(
    x_actor_id: str | None = Header(None, alias="X-Actor-Id"),
    x_actor_roles: str | None = Header(None, alias="X-Actor-Roles"),
    x_service_name: str | None = Header(None, alias="X-Service-Name"),
) -> ActorContext:
    roles: list[str] = []
    if x_actor_roles:
        roles = [r.strip() for r in x_actor_roles.split(",") if r.strip()]
    return ActorContext(
        actor_id=x_actor_id,
        roles=roles or ["admin_operacao"],
        service_name=x_service_name or "privacy_compliance_admin_service",
    )
