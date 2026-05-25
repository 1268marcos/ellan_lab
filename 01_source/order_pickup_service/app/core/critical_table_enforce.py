from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from shared.security.critical_table_guard import ActorContext, CriticalTableDenied, enforce_critical_access


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    import uuid

    return str(uuid.uuid4())


def _load_policies(conn: Any, *, table_name: str, operation: str) -> list[Any]:
    rows = conn.execute(
        text(
            """
            SELECT role, scope_type, allowed, priority, is_active
            FROM app_critical_table_policy
            WHERE table_name = :t AND operation = :op AND is_active = true
            ORDER BY priority ASC
            """
        ),
        {"t": table_name, "op": operation},
    ).fetchall()

    class _Pol:
        def __init__(self, r: Any) -> None:
            self.role = r[0]
            self.scope_type = r[1]
            self.allowed = r[2]
            self.priority = r[3]
            self.is_active = r[4]

    return [_Pol(r) for r in rows]


def _write_access_log(conn: Any, **kwargs: Any) -> None:
    conn.execute(
        text(
            """
            INSERT INTO app_critical_table_access_log
            (id, table_name, operation, actor_id, actor_roles_json, target_user_id, row_id, decision, reason, service_name, occurred_at)
            VALUES (:id, :table_name, :operation, :actor_id, :actor_roles_json, :target_user_id, :row_id, :decision, :reason, :service_name, :occurred_at)
            """
        ),
        kwargs,
    )


def enforce_users(
    db: Session,
    *,
    operation: str,
    actor: ActorContext,
    target_user_id: str | None = None,
    row_id: str | None = None,
) -> None:
    conn = db.connection()
    try:
        enforce_critical_access(
            conn,
            table_name="users",
            operation=operation,
            actor=actor,
            target_user_id=target_user_id,
            row_id=row_id,
            policy_loader=_load_policies,
            access_log_writer=_write_access_log,
            new_id=_new_id,
        )
    except CriticalTableDenied as exc:
        raise PermissionError(str(exc)) from exc
