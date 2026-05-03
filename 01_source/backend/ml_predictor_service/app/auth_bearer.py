"""Validação de sessão Bearer (mesmo token que order_pickup: hash SHA-256 em auth_sessions)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from fastapi import Header, HTTPException

from app import db

# Alinhado ao painel Inteligência (App.jsx IntelligenceRoute)
_LTV_PRIVILEGED_ROLES = frozenset(
    {
        "admin_operacao",
        "admin_financeiro",
        "auditoria",
    }
)


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    t = authorization[7:].strip()
    return t or None


def _hash_session_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def resolve_user_from_bearer(authorization: str | None) -> dict[str, Any] | None:
    """Retorna {user_id, email} se sessão válida; None se token ausente."""
    raw = _extract_bearer(authorization)
    if not raw:
        return None
    th = _hash_session_token(raw)
    now = _utc_naive_now()
    row = db.fetch_one(
        """
        SELECT u.id::text AS user_id, u.email::text AS email
        FROM auth_sessions s
        INNER JOIN users u ON u.id::text = s.user_id::text
        WHERE s.session_token_hash = %s
          AND s.revoked_at IS NULL
          AND s.expires_at > %s
          AND u.is_active = true
          AND u.deleted_at IS NULL
          AND u.anonymized_at IS NULL
        LIMIT 1
        """,
        (th, now),
    )
    return dict(row) if row else None


def user_has_ltv_privileged_role(user_id: str) -> bool:
    rows = db.fetch_all(
        """
        SELECT lower(trim(role)) AS role
        FROM user_roles
        WHERE user_id::text = %s
          AND COALESCE(is_active, true) = true
          AND revoked_at IS NULL
        """,
        (user_id,),
    )
    roles = {str(r.get("role") or "") for r in rows}
    return bool(roles & _LTV_PRIVILEGED_ROLES)


def require_session_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    u = resolve_user_from_bearer(authorization)
    if not u:
        raise HTTPException(
            status_code=401,
            detail="missing_or_invalid_session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return u


def assert_can_read_customer_ltv(*, caller_user_id: str, customer_id: str) -> None:
    """Próprio usuário ou papel Inteligência/OPS (admin_operacao, admin_financeiro, auditoria)."""
    if caller_user_id == customer_id:
        return
    if user_has_ltv_privileged_role(caller_user_id):
        return
    raise HTTPException(
        status_code=403,
        detail="forbidden: apenas o próprio cliente ou roles admin_operacao, admin_financeiro, auditoria",
    )
