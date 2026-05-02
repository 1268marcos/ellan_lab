from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.schemas.locker_operators import (
    LockerOperatorCreateIn,
    LockerOperatorDeleteOut,
    LockerOperatorListOut,
    LockerOperatorOut,
    LockerOperatorUpdateIn,
)

READ_ROLES = {"admin_operacao", "suporte", "auditoria"}
WRITE_ROLES = {"admin_operacao"}

router = APIRouter(prefix="/operators", tags=["operators"])


def _to_iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        v = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).isoformat()
    return str(value)


def _row_to_out(row: dict[str, Any]) -> LockerOperatorOut:
    return LockerOperatorOut(
        id=str(row.get("id") or ""),
        name=str(row.get("name") or ""),
        document=(str(row["document"]) if row.get("document") is not None else None),
        email=(str(row["email"]) if row.get("email") is not None else None),
        phone=(str(row["phone"]) if row.get("phone") is not None else None),
        operator_type=str(row.get("operator_type") or "LOGISTICS"),
        country=str(row.get("country") or "BR"),
        active=True if row.get("active") is None else bool(row.get("active")),
        commission_rate=(float(row["commission_rate"]) if row.get("commission_rate") is not None else None),
        currency=str(row.get("currency") or "BRL"),
        status=str(row.get("status") or "DRAFT"),
        contract_start_at=_to_iso(row["contract_start_at"]) if row.get("contract_start_at") is not None else None,
        contract_end_at=_to_iso(row["contract_end_at"]) if row.get("contract_end_at") is not None else None,
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


@router.get("", response_model=LockerOperatorListOut, dependencies=[Depends(require_user_roles(allowed_roles=READ_ROLES))])
def list_operators_ops(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                """
                SELECT id, name, document, email, phone, operator_type, country, active,
                       commission_rate, currency, status, contract_start_at, contract_end_at,
                       created_at, updated_at
                FROM locker_operators
                ORDER BY name, id
                """
            )
        )
        .mappings()
        .all()
    )
    return LockerOperatorListOut(ok=True, items=[_row_to_out(dict(r)) for r in rows])


@router.post("", response_model=LockerOperatorOut, dependencies=[Depends(require_user_roles(allowed_roles=WRITE_ROLES))])
def create_operator_ops(payload: LockerOperatorCreateIn, db: Session = Depends(get_db)):
    oid = str(payload.id).strip()
    if db.execute(text("SELECT 1 FROM locker_operators WHERE id = :id LIMIT 1"), {"id": oid}).scalar():
        raise HTTPException(status_code=409, detail={"type": "OPERATOR_EXISTS", "message": f"Operador {oid} já existe."})
    cs = payload.contract_start_at
    ce = payload.contract_end_at
    db.execute(
        text(
            """
            INSERT INTO locker_operators (
                id, name, document, email, phone, operator_type, country, active,
                commission_rate, currency, status, contract_start_at, contract_end_at,
                created_at, updated_at
            ) VALUES (
                :id, :name, :document, :email, :phone, :operator_type, :country, TRUE,
                :commission_rate, :currency, :status, :contract_start_at, :contract_end_at,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": oid,
            "name": str(payload.name).strip(),
            "document": payload.document.strip() if payload.document else None,
            "email": payload.email.strip() if payload.email else None,
            "phone": payload.phone.strip() if payload.phone else None,
            "operator_type": str(payload.operator_type or "LOGISTICS").strip()[:32] or "LOGISTICS",
            "country": str(payload.country or "BR").strip()[:2].upper() or "BR",
            "commission_rate": payload.commission_rate,
            "currency": str(payload.currency or "BRL").strip()[:8] or "BRL",
            "status": str(payload.status or "DRAFT").strip()[:30] or "DRAFT",
            "contract_start_at": cs,
            "contract_end_at": ce,
        },
    )
    db.commit()
    row = db.execute(text("SELECT * FROM locker_operators WHERE id = :id"), {"id": oid}).mappings().first()
    return _row_to_out(dict(row or {}))


@router.patch(
    "/{operator_id}",
    response_model=LockerOperatorOut,
    dependencies=[Depends(require_user_roles(allowed_roles=WRITE_ROLES))],
)
def update_operator_ops(operator_id: str, payload: LockerOperatorUpdateIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM locker_operators WHERE id = :id"), {"id": operator_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "OPERATOR_NOT_FOUND", "message": "Operador não encontrado."})
    r = dict(row)
    patch = payload.model_dump(exclude_unset=True)
    if "name" in patch:
        r["name"] = str(patch["name"] or "").strip() or str(r.get("name") or "")
    if "document" in patch:
        v = patch["document"]
        r["document"] = v.strip() if isinstance(v, str) and v.strip() else None
    if "email" in patch:
        v = patch["email"]
        r["email"] = v.strip() if isinstance(v, str) and v.strip() else None
    if "phone" in patch:
        v = patch["phone"]
        r["phone"] = v.strip() if isinstance(v, str) and v.strip() else None
    if "operator_type" in patch and patch["operator_type"] is not None:
        r["operator_type"] = str(patch["operator_type"]).strip()[:32] or r.get("operator_type")
    if "country" in patch and patch["country"] is not None:
        r["country"] = str(patch["country"]).strip()[:2].upper() or r.get("country")
    if "active" in patch:
        r["active"] = bool(patch["active"])
    if "commission_rate" in patch:
        r["commission_rate"] = patch["commission_rate"]
    if "currency" in patch and patch["currency"] is not None:
        r["currency"] = str(patch["currency"]).strip()[:8] or r.get("currency")
    if "status" in patch and patch["status"] is not None:
        r["status"] = str(patch["status"]).strip()[:30] or r.get("status")
    if "contract_start_at" in patch:
        r["contract_start_at"] = patch["contract_start_at"]
    if "contract_end_at" in patch:
        r["contract_end_at"] = patch["contract_end_at"]
    db.execute(
        text(
            """
            UPDATE locker_operators SET
                name = :name, document = :document, email = :email, phone = :phone,
                operator_type = :operator_type, country = :country, active = :active,
                commission_rate = :commission_rate, currency = :currency, status = :status,
                contract_start_at = :contract_start_at, contract_end_at = :contract_end_at,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {
            "id": operator_id,
            "name": str(r.get("name") or ""),
            "document": r.get("document"),
            "email": r.get("email"),
            "phone": r.get("phone"),
            "operator_type": str(r.get("operator_type") or "LOGISTICS"),
            "country": str(r.get("country") or "BR"),
            "active": bool(r.get("active", True)),
            "commission_rate": r.get("commission_rate"),
            "currency": str(r.get("currency") or "BRL"),
            "status": str(r.get("status") or "DRAFT"),
            "contract_start_at": r.get("contract_start_at"),
            "contract_end_at": r.get("contract_end_at"),
        },
    )
    db.commit()
    row2 = db.execute(text("SELECT * FROM locker_operators WHERE id = :id"), {"id": operator_id}).mappings().first()
    return _row_to_out(dict(row2 or {}))


@router.delete(
    "/{operator_id}",
    response_model=LockerOperatorDeleteOut,
    dependencies=[Depends(require_user_roles(allowed_roles=WRITE_ROLES))],
)
def delete_operator_ops(operator_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM locker_operators WHERE id = :id"), {"id": operator_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "OPERATOR_NOT_FOUND", "message": "Operador não encontrado."})
    lk = int(db.execute(text("SELECT COUNT(*) FROM lockers WHERE operator_id = :id"), {"id": operator_id}).scalar() or 0)
    pk = int(db.execute(text("SELECT COUNT(*) FROM pickups WHERE operator_id = :id"), {"id": operator_id}).scalar() or 0)
    if lk or pk:
        raise HTTPException(
            status_code=409,
            detail={"type": "OPERATOR_IN_USE", "message": f"Operador referenciado (lockers={lk}, pickups={pk})."},
        )
    db.execute(text("DELETE FROM locker_operators WHERE id = :id"), {"id": operator_id})
    db.commit()
    return LockerOperatorDeleteOut(ok=True, id=operator_id)
