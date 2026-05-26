"""Autenticação de parceiros B2B para API de assinaturas (API keys)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db


@dataclass(frozen=True)
class SubscriptionPartnerAuth:
    partner_code: str
    key_id: str
    scopes: frozenset[str]


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_scopes(raw: str | None) -> frozenset[str]:
    if not raw:
        return frozenset()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return frozenset(str(s) for s in data)
    except (json.JSONDecodeError, TypeError):
        pass
    return frozenset()


def require_subscription_partner(*, required_scope: str | None = None):
    def _dependency(
        partner_code: Annotated[str, Header(alias="X-Partner-Code", min_length=1, max_length=64)],
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> SubscriptionPartnerAuth:
        raw_key = (x_api_key or "").strip()
        if not raw_key and authorization:
            auth = authorization.strip()
            if auth.lower().startswith("bearer "):
                raw_key = auth[7:].strip()
            else:
                raw_key = auth
        if not raw_key:
            raise HTTPException(
                status_code=401,
                detail={"type": "API_KEY_REQUIRED", "message": "Envie X-API-Key ou Authorization: Bearer <key>."},
            )

        pcode = partner_code.strip().lower()
        key_hash = _hash_key(raw_key)
        row = db.execute(
            text(
                """
                SELECT id, partner_code, scopes_json, expires_at, revoked_at
                FROM subscription_api_keys
                WHERE partner_code = :p AND key_hash = :h AND revoked_at IS NULL
                LIMIT 1
                """
            ),
            {"p": pcode, "h": key_hash},
        ).mappings().first()

        if not row:
            raise HTTPException(
                status_code=401,
                detail={"type": "INVALID_API_KEY", "message": "API key inválida para o parceiro informado."},
            )

        expires_at = row.get("expires_at")
        if expires_at is not None:
            exp = expires_at
            if isinstance(exp, str):
                exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if isinstance(exp, datetime):
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=401,
                        detail={"type": "API_KEY_EXPIRED", "message": "API key expirada."},
                    )

        scopes = _parse_scopes(row.get("scopes_json"))
        if required_scope and required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "type": "INSUFFICIENT_SCOPE",
                    "message": f"Escopo obrigatório: {required_scope}",
                    "scopes": sorted(scopes),
                },
            )

        now = datetime.now(timezone.utc)
        db.execute(
            text("UPDATE subscription_api_keys SET last_used_at = :now WHERE id = :id"),
            {"id": row["id"], "now": now},
        )
        db.commit()

        return SubscriptionPartnerAuth(
            partner_code=str(row["partner_code"]),
            key_id=str(row["id"]),
            scopes=scopes,
        )

    return _dependency
