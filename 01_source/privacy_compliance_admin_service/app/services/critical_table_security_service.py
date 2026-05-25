from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.critical_table_security import (
    AppCriticalTableAccessLog,
    AppCriticalTablePolicy,
    AppCriticalTableRegistry,
)
from app.services.crypto_util import new_id
from shared.security.critical_table_guard import ActorContext, CriticalTableDenied, enforce_critical_access


def _load_policies(db: Session, *, table_name: str, operation: str) -> list[AppCriticalTablePolicy]:
    return (
        db.query(AppCriticalTablePolicy)
        .filter(
            AppCriticalTablePolicy.table_name == table_name,
            AppCriticalTablePolicy.operation == operation,
            AppCriticalTablePolicy.is_active.is_(True),
        )
        .order_by(AppCriticalTablePolicy.priority.asc())
        .all()
    )


def _write_access_log(db: Session, **kwargs: Any) -> None:
    db.add(AppCriticalTableAccessLog(**kwargs))
    db.flush()


def enforce(
    db: Session,
    *,
    table_name: str,
    operation: str,
    actor: ActorContext,
    target_user_id: str | None = None,
    row_id: str | None = None,
) -> None:
    try:
        enforce_critical_access(
            db,
            table_name=table_name,
            operation=operation,
            actor=actor,
            target_user_id=target_user_id,
            row_id=row_id,
            policy_loader=_load_policies,
            access_log_writer=_write_access_log,
            new_id=new_id,
        )
    except CriticalTableDenied as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "critical_table_denied",
                "table": exc.table_name,
                "operation": exc.operation,
                "reason": exc.reason,
            },
        ) from exc


def seed_registry_and_policies(db: Session) -> dict[str, int]:
    counts = {"registry": 0, "policies": 0}
    for table_name, description in (
        ("users", "PII critico — enforcement APPLICATION"),
        ("privacy_consents", "LGPD/GDPR consents — enforcement APPLICATION"),
        ("audit_logs", "Trilha imutavel — enforcement APPLICATION"),
    ):
        if not db.get(AppCriticalTableRegistry, table_name):
            db.add(
                AppCriticalTableRegistry(
                    table_name=table_name,
                    rls_enabled=False,
                    enforcement_layer="APPLICATION",
                    description=description,
                )
            )
            counts["registry"] += 1
    seed_rows = [
        ("pol-pc-sel-admin", "privacy_consents", "SELECT", "admin_operacao", "GLOBAL", True, 10),
        ("pol-pc-sel-audit", "privacy_consents", "SELECT", "auditoria", "GLOBAL", True, 20),
        ("pol-pc-sel-self", "privacy_consents", "SELECT", "usuario_comum", "SELF", True, 30),
        ("pol-pc-ins-admin", "privacy_consents", "INSERT", "admin_operacao", "GLOBAL", True, 10),
        ("pol-pc-ins-sys", "privacy_consents", "INSERT", "SYSTEM", "GLOBAL", True, 15),
        ("pol-pc-ins-self", "privacy_consents", "INSERT", "usuario_comum", "SELF", True, 20),
        ("pol-pc-upd-admin", "privacy_consents", "UPDATE", "admin_operacao", "GLOBAL", True, 10),
        ("pol-pc-del-admin", "privacy_consents", "DELETE", "admin_operacao", "GLOBAL", True, 10),
    ]
    for pid, table_name, operation, role, scope_type, allowed, priority in seed_rows:
        if db.get(AppCriticalTablePolicy, pid):
            continue
        db.add(
            AppCriticalTablePolicy(
                id=pid,
                table_name=table_name,
                operation=operation,
                role=role,
                scope_type=scope_type,
                allowed=allowed,
                priority=priority,
            )
        )
        counts["policies"] += 1
    db.commit()
    return counts
