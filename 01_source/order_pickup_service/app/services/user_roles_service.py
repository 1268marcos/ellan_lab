from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "no such table" in message
        or "undefined table" in message
        or "does not exist" in message
        or "relation \"public.user_roles\"" in message
    )


def _query_roles(db: Session, *, user_id: str, table_name: str) -> list[dict[str, Any]]:
    stmt = text(
        f"""
        SELECT id, user_id, role, scope_type, scope_id, is_active, granted_at, revoked_at
        FROM {table_name}
        WHERE user_id = :user_id
          AND COALESCE(is_active, true) = true
          AND revoked_at IS NULL
        ORDER BY granted_at DESC, id DESC
        """
    )
    rows = db.execute(stmt, {"user_id": user_id}).mappings().all()
    return [dict(row) for row in rows]


def list_active_user_roles(db: Session, *, user_id: str) -> list[dict[str, Any]]:
    if not user_id:
        return []

    try:
        return _query_roles(db, user_id=user_id, table_name="public.user_roles")
    except SQLAlchemyError as exc:
        if not _is_missing_table_error(exc):
            logger.exception("list_active_user_roles_query_failed")
            return []

    try:
        return _query_roles(db, user_id=user_id, table_name="user_roles")
    except SQLAlchemyError as exc:
        if not _is_missing_table_error(exc):
            logger.exception("list_active_user_roles_query_failed_fallback")
        return []


def user_has_any_role(
    db: Session,
    *,
    user_id: str,
    allowed_roles: set[str],
    scope_type: str | None = None,
    scope_id: str | None = None,
) -> bool:
    roles = list_active_user_roles(db, user_id=user_id)
    if not roles:
        return False

    normalized_allowed = {str(role).strip().lower() for role in allowed_roles if str(role).strip()}
    for role_row in roles:
        current_role = str(role_row.get("role") or "").strip().lower()
        if current_role not in normalized_allowed:
            continue

        if scope_type:
            current_scope_type = str(role_row.get("scope_type") or "").strip().lower()
            if current_scope_type != str(scope_type).strip().lower():
                continue
        if scope_id:
            current_scope_id = str(role_row.get("scope_id") or "").strip()
            if current_scope_id != str(scope_id).strip():
                continue
        return True
    return False
