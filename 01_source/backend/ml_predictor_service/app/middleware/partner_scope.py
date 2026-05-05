"""Escopo de lockers por parceiro (partner_service_areas)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Query

from app import db
from app.auth_bearer import (
    require_session_user,
    user_has_feedback_ops_role,
    user_has_ltv_privileged_role,
)


@dataclass(frozen=True)
class PartnerLockerScope:
    user_id: str
    partner_id: str | None
    locker_ids: list[str] | None

    def raise_if_locker_forbidden(self, locker_id: str | None) -> None:
        if self.locker_ids is None:
            return
        lid = (locker_id or "").strip()
        if not lid or lid not in self.locker_ids:
            raise HTTPException(status_code=403, detail="locker_not_in_partner_scope")


def _fetch_lockers_for_partner(partner_id: str) -> list[str]:
    rows = db.fetch_all(
        """
        SELECT locker_id::text AS locker_id
        FROM partner_service_areas
        WHERE partner_id::text = %s
          AND is_active = true
          AND (valid_until IS NULL OR valid_until >= CURRENT_DATE)
        """,
        (partner_id,),
    )
    return [str(r["locker_id"]) for r in rows]


def get_partner_lockers(
    user: dict[str, Any] = Depends(require_session_user),
    partner_id: str | None = Query(None),
) -> PartnerLockerScope:
    uid = str(user["user_id"])
    pid = (partner_id or "").strip() or None
    if not pid:
        if user_has_feedback_ops_role(uid) or user_has_ltv_privileged_role(uid):
            return PartnerLockerScope(user_id=uid, partner_id=None, locker_ids=None)
        raise HTTPException(status_code=400, detail="partner_id_required")
    lockers = _fetch_lockers_for_partner(pid)
    return PartnerLockerScope(user_id=uid, partner_id=pid, locker_ids=lockers)


def scope_sql_predicate(locker_ids: list[str] | None, column_sql: str) -> tuple[str, list[Any]]:
    if locker_ids is None:
        return "", []
    return f" AND {column_sql} = ANY(%s)", [locker_ids]
