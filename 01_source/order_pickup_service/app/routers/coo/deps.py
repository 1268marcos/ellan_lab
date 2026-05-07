"""Dependências compartilhadas do portal COO (auth)."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.auth_service import get_user_by_session_token
from app.services.user_roles_service import user_has_any_role


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def _resolve_partner_by_raw_api_key(db: Session, raw_key: str) -> dict[str, Any] | None:
    if not raw_key:
        return None
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    pid_row = db.execute(
        text(
            """
            SELECT partner_id
            FROM partner_api_keys
            WHERE key_hash = :key_hash
              AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"key_hash": key_hash},
    ).mappings().first()
    if not pid_row:
        return None
    partner_id = str(pid_row["partner_id"])
    prow = db.execute(
        text(
            """
            SELECT id, name, code, tier, status
            FROM ecommerce_partners
            WHERE id = :id
            LIMIT 1
            """
        ),
        {"id": partner_id},
    ).mappings().first()
    return dict(prow) if prow else None


def _partner_may_access_coo_portal(row: dict[str, Any]) -> bool:
    pid = str(row.get("id") or "").lower()
    code = str(row.get("code") or "").upper()
    tier = str(row.get("tier") or "").upper()
    if "coo" in pid:
        return True
    if code in {"COO", "ELLAN_COO", "OPS", "OPS_LEAD"}:
        return True
    return tier in {"OPERATIONS", "OPS"}


def require_coo_access(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> None:
    """Sessão Bearer com role coo/ceo/ops ou parceiro operacional (API key)."""
    bearer = _bearer_token(authorization)
    raw_key = (x_api_key or "").strip() or (bearer or "").strip()

    if bearer:
        user = get_user_by_session_token(db, raw_token=bearer)
        if user is not None and user.is_active:
            if user_has_any_role(db, user_id=user.id, allowed_roles={"coo", "ceo", "ops"}):
                return

    if raw_key:
        prow = _resolve_partner_by_raw_api_key(db, raw_key)
        if prow and _partner_may_access_coo_portal(prow):
            return

    raise HTTPException(
        status_code=403,
        detail={
            "type": "COO_ACCESS_REQUIRED",
            "message": "Acesso restrito: role coo, ceo ou ops; ou parceiro operacional (API key).",
        },
    )
