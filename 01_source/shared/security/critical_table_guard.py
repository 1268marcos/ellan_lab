from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


class CriticalTableDenied(PermissionError):
    def __init__(self, *, table_name: str, operation: str, reason: str) -> None:
        self.table_name = table_name
        self.operation = operation
        self.reason = reason
        super().__init__(f"{table_name}:{operation}:{reason}")


@dataclass
class ActorContext:
    actor_id: str | None = None
    roles: list[str] = field(default_factory=list)
    service_name: str | None = None

    def effective_roles(self) -> list[str]:
        roles = list(self.roles)
        if self.service_name and "SYSTEM" not in roles:
            roles.append("SYSTEM")
        if not roles:
            roles.append("usuario_comum")
        return roles


class _PolicyRow(Protocol):
    role: str
    scope_type: str
    allowed: bool
    priority: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _match_scope(
    *,
    scope_type: str,
    actor_id: str | None,
    target_user_id: str | None,
    row_id: str | None,
) -> bool:
    st = (scope_type or "GLOBAL").upper()
    if st == "GLOBAL":
        return True
    if st == "SELF":
        if not actor_id or not target_user_id:
            return False
        return actor_id == target_user_id
    if st == "ROW":
        return bool(row_id) and actor_id == row_id
    return False


def _evaluate_policies(
    policies: list[_PolicyRow],
    *,
    operation: str,
    actor: ActorContext,
    target_user_id: str | None,
    row_id: str | None,
) -> tuple[bool, str]:
    op = operation.upper()
    roles = actor.effective_roles()
    candidates: list[tuple[int, bool, str]] = []

    for pol in policies:
        if not getattr(pol, "is_active", True):
            continue
        if pol.role not in roles:
            continue
        if not _match_scope(
            scope_type=pol.scope_type,
            actor_id=actor.actor_id,
            target_user_id=target_user_id,
            row_id=row_id,
        ):
            continue
        candidates.append((pol.priority, pol.allowed, pol.role))

    if not candidates:
        return False, "no_matching_policy"

    candidates.sort(key=lambda x: x[0])
    _prio, allowed, matched_role = candidates[0]
    if not allowed:
        return False, f"explicit_deny:{matched_role}"
    return True, f"allow:{matched_role}"


def enforce_critical_access(
    db: Any,
    *,
    table_name: str,
    operation: str,
    actor: ActorContext,
    target_user_id: str | None = None,
    row_id: str | None = None,
    policy_loader: Any,
    access_log_writer: Any,
    new_id: Any,
) -> None:
    policies = policy_loader(db, table_name=table_name, operation=operation.upper())
    allowed, reason = _evaluate_policies(
        policies,
        operation=operation,
        actor=actor,
        target_user_id=target_user_id,
        row_id=row_id,
    )
    decision = "ALLOWED" if allowed else "DENIED"
    access_log_writer(
        db,
        id=new_id(),
        table_name=table_name,
        operation=operation.upper(),
        actor_id=actor.actor_id,
        actor_roles_json=json.dumps(actor.effective_roles()),
        target_user_id=target_user_id,
        row_id=row_id,
        decision=decision,
        reason=reason,
        service_name=actor.service_name,
        occurred_at=_utcnow(),
    )
    if not allowed:
        raise CriticalTableDenied(table_name=table_name, operation=operation.upper(), reason=reason)
