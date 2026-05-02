"""Leitura interna de contratos e planos de aluguel (X-Internal-Token)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.internal_auth import require_internal_token

router = APIRouter(
    prefix="/rentals",
    tags=["internal-rentals"],
    dependencies=[Depends(require_internal_token)],
)


def _serialize_value(v: Any) -> Any:
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def _serialize_row(row: Any) -> dict[str, Any]:
    return {k: _serialize_value(v) for k, v in dict(row).items()}


def _is_active_flag(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return int(v) != 0
    return str(v).strip().lower() in {"1", "true", "t", "yes"}


def _build_contract_filters(
    *,
    status: Optional[str],
    locker_id: Optional[str],
    renter_user_id: Optional[str],
) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("c.status = :status")
        params["status"] = status.strip()
    if locker_id:
        clauses.append("c.locker_id = :locker_id")
        params["locker_id"] = locker_id.strip()
    if renter_user_id:
        clauses.append("c.renter_user_id = :renter_user_id")
        params["renter_user_id"] = renter_user_id.strip()
    return " AND ".join(clauses), params


@router.get("/contracts")
def list_rental_contracts(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="PENDING | ACTIVE | SUSPENDED | OVERDUE | ENDED | CANCELLED"),
    locker_id: Optional[str] = Query(None),
    renter_user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    where_sql, params = _build_contract_filters(status=status, locker_id=locker_id, renter_user_id=renter_user_id)
    count_row = db.execute(
        text(f"SELECT COUNT(*) AS n FROM rental_contracts c WHERE {where_sql}"),
        params,
    ).mappings().first()
    total = int(count_row["n"]) if count_row else 0
    params_list = {**params, "limit": limit, "offset": offset}
    rows = db.execute(
        text(
            f"""
            SELECT c.id, c.locker_id, c.renter_name, c.status, c.billing_cycle, c.amount_cents,
                   c.next_billing_at, c.renter_user_id, c.slot_label, c.plan_id, c.currency
            FROM rental_contracts c
            WHERE {where_sql}
            ORDER BY c.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params_list,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/contracts/{contract_id}")
def get_rental_contract(contract_id: str, db: Session = Depends(get_db)):
    crow = db.execute(
        text("SELECT * FROM rental_contracts WHERE id = :id LIMIT 1"),
        {"id": contract_id},
    ).mappings().first()
    if not crow:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND", "message": contract_id})
    contract = _serialize_row(crow)
    plan_id = crow.get("plan_id")
    plan = None
    if plan_id:
        prow = db.execute(
            text("SELECT * FROM rental_plans WHERE id = :id LIMIT 1"),
            {"id": str(plan_id)},
        ).mappings().first()
        if prow:
            plan = _serialize_row(prow)
    slot = None
    locker_id = crow.get("locker_id")
    slot_label = crow.get("slot_label")
    if locker_id and slot_label:
        srow = db.execute(
            text(
                """
                SELECT id, locker_id, slot_label, slot_size, status, current_rental_id
                FROM locker_slots
                WHERE locker_id = :locker_id AND slot_label = :slot_label
                LIMIT 1
                """
            ),
            {"locker_id": str(locker_id), "slot_label": str(slot_label)},
        ).mappings().first()
        if srow:
            slot = _serialize_row(srow)
    return {"contract": contract, "plan": plan, "slot": slot}


@router.get("/plans")
def list_rental_plans(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT name, locker_id, slot_size, amount_cents, billing_cycle, id, currency, active
            FROM rental_plans
            ORDER BY name
            """
        )
    ).mappings().all()
    active_rows = [r for r in rows if _is_active_flag(r.get("active"))]
    return {"items": [_serialize_row(r) for r in active_rows]}
