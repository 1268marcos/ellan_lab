"""OPS: planos, contratos, webhooks e API keys do domínio rental."""
from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rental_locker_ecosystem import ecosystem_catalog_payload
from app.core.rental_schema import ensure_rental_schema
from app.core.rental_seed import seed_rentals
from app.routers.rental_ops_common import serialize_row as _serialize_row
from app.routers.rental_ops_common import utc_now as _utc_now
from app.services.rental_events import log_rental_contract_event
from app.services.rental_insurance import (
    calculate_content_insurance_premium,
    create_content_insurance,
)
from app.services.rental_pricing import resolve_contract_pricing_context
from app.schemas.rentals_ops import (
    RentalContractCancelIn,
    RentalContractIn,
    RentalContractPricingPreviewIn,
    RentalContractUpdate,
    RentalPlanIn,
    RentalPlanUpdate,
    RentalWebhookIn,
    RentalWebhookUpdate,
)

router = APIRouter(tags=["rentals-ops"])


def _is_active_flag(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return int(v) != 0
    return str(v).strip().lower() in {"1", "true", "t", "yes"}


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_api_key() -> tuple[str, str, str]:
    raw = f"rnt_{secrets.token_urlsafe(24)}"
    return raw, raw[:12], _hash_secret(raw)


def _build_contract_filters(
    *,
    status: Optional[str],
    locker_id: Optional[str],
    renter_user_id: Optional[str],
    tenant_id: Optional[str] = None,
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
    if tenant_id:
        clauses.append("c.tenant_id = :tenant_id")
        params["tenant_id"] = tenant_id.strip()
    return " AND ".join(clauses), params


def _plan_row(db: Session, plan_id: str) -> dict[str, Any] | None:
    row = db.execute(
        text("SELECT * FROM rental_plans WHERE id = :id LIMIT 1"),
        {"id": plan_id},
    ).mappings().first()
    return _serialize_row(row) if row else None


def _contract_row(db: Session, contract_id: str) -> dict[str, Any] | None:
    row = db.execute(
        text("SELECT * FROM rental_contracts WHERE id = :id LIMIT 1"),
        {"id": contract_id},
    ).mappings().first()
    return _serialize_row(row) if row else None


def _ensure_locker(db: Session, locker_id: str) -> None:
    if not db.execute(
        text("SELECT id FROM lockers WHERE id = :id LIMIT 1"),
        {"id": locker_id},
    ).mappings().first():
        raise HTTPException(
            status_code=404,
            detail={"type": "LOCKER_NOT_FOUND", "message": locker_id},
        )


def _insert_rental_contract_row(db: Session, params: dict[str, Any]) -> None:
    """INSERT com colunas de pricing/seguro quando a migração já rodou."""
    full = {
        **params,
        "pricing_rule_code": params.get("pricing_rule_code"),
        "insurance_premium_cents": params.get("insurance_premium_cents", 0),
    }
    try:
        db.execute(
            text(
                """
                INSERT INTO rental_contracts (
                    id, locker_id, slot_label, plan_id, tenant_id, renter_user_id,
                    renter_name, renter_document, renter_phone, renter_email,
                    amount_cents, currency, billing_cycle, next_billing_at, auto_renew,
                    status, started_at, pricing_rule_code, insurance_premium_cents,
                    created_at, updated_at
                ) VALUES (
                    :id, :locker_id, :slot_label, :plan_id, :tenant_id, :renter_user_id,
                    :renter_name, :renter_document, :renter_phone, :renter_email,
                    :amount_cents, :currency, :billing_cycle, :next_billing_at, :auto_renew,
                    :status, :started_at, :pricing_rule_code, :insurance_premium_cents,
                    :now, :now
                )
                """
            ),
            full,
        )
    except Exception:
        db.execute(
            text(
                """
                INSERT INTO rental_contracts (
                    id, locker_id, slot_label, plan_id, tenant_id, renter_user_id,
                    renter_name, renter_document, renter_phone, renter_email,
                    amount_cents, currency, billing_cycle, next_billing_at, auto_renew,
                    status, started_at, created_at, updated_at
                ) VALUES (
                    :id, :locker_id, :slot_label, :plan_id, :tenant_id, :renter_user_id,
                    :renter_name, :renter_document, :renter_phone, :renter_email,
                    :amount_cents, :currency, :billing_cycle, :next_billing_at, :auto_renew,
                    :status, :started_at, :now, :now
                )
                """
            ),
            params,
        )


def _apply_plan_to_contract_fields(db: Session, plan_id: str | None) -> dict[str, Any]:
    if not plan_id:
        return {}
    prow = db.execute(
        text(
            "SELECT amount_cents, billing_cycle, currency FROM rental_plans WHERE id = :id LIMIT 1"
        ),
        {"id": plan_id},
    ).mappings().first()
    if not prow:
        raise HTTPException(
            status_code=404,
            detail={"type": "RENTAL_PLAN_NOT_FOUND", "message": plan_id},
        )
    return {
        "amount_cents": int(prow["amount_cents"]),
        "billing_cycle": str(prow["billing_cycle"]),
        "currency": str(prow.get("currency") or "BRL"),
    }


@router.get("/ecosystem/catalog")
def get_rental_ecosystem_catalog():
    """Catálogo de referência (InPost, DHL, Magalu, MELI, Amazon, DPD, Correios, CTT, Worten, ECI, …)."""
    return {"ok": True, "catalog": ecosystem_catalog_payload()}


@router.post("/seed")
def post_rentals_seed(db: Session = Depends(get_db)):
    migrations = ensure_rental_schema(db)
    try:
        result = seed_rentals(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"type": "RENTAL_SEED_FAILED", "message": str(exc), "migrations_applied": migrations},
        ) from exc
    return {"ok": True, "seeded": result, "migrations_applied": migrations}


@router.get("/plans")
def list_rental_plans(
    db: Session = Depends(get_db),
    active_only: bool = Query(True),
    locker_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if active_only:
        clauses.append("active = TRUE")
    if locker_id:
        clauses.append("(locker_id = :locker_id OR locker_id IS NULL)")
        params["locker_id"] = locker_id.strip()
    where_sql = " AND ".join(clauses)
    total = int(
        db.execute(text(f"SELECT COUNT(*) AS n FROM rental_plans WHERE {where_sql}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT id, locker_id, slot_size, name, description, billing_cycle, amount_cents,
                   currency, max_duration_days, grace_period_hours, active, created_at, updated_at
            FROM rental_plans
            WHERE {where_sql}
            ORDER BY name
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [_serialize_row(r) for r in rows]
    if active_only:
        items = [x for x in items if _is_active_flag(x.get("active"))]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_rental_plan(body: RentalPlanIn, db: Session = Depends(get_db)):
    if body.locker_id:
        _ensure_locker(db, body.locker_id)
    plan_id = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_plans (
                id, locker_id, slot_size, name, description, billing_cycle, amount_cents,
                currency, max_duration_days, grace_period_hours, active, created_at, updated_at
            ) VALUES (
                :id, :locker_id, :slot_size, :name, :description, :billing_cycle, :amount_cents,
                :currency, :max_duration_days, :grace_period_hours, :active, :now, :now
            )
            """
        ),
        {
            "id": plan_id,
            "locker_id": body.locker_id,
            "slot_size": body.slot_size,
            "name": body.name,
            "description": body.description,
            "billing_cycle": body.billing_cycle,
            "amount_cents": body.amount_cents,
            "currency": body.currency,
            "max_duration_days": body.max_duration_days,
            "grace_period_hours": body.grace_period_hours,
            "active": body.active,
            "now": now,
        },
    )
    db.commit()
    return _plan_row(db, plan_id)


@router.patch("/plans/{plan_id}")
def update_rental_plan(plan_id: str, body: RentalPlanUpdate, db: Session = Depends(get_db)):
    if not _plan_row(db, plan_id):
        raise HTTPException(status_code=404, detail={"type": "RENTAL_PLAN_NOT_FOUND", "message": plan_id})
    if body.locker_id:
        _ensure_locker(db, body.locker_id)
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return _plan_row(db, plan_id)
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = plan_id
    fields["updated_at"] = _utc_now()
    db.execute(
        text(f"UPDATE rental_plans SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    db.commit()
    return _plan_row(db, plan_id)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_200_OK)
def delete_rental_plan(plan_id: str, db: Session = Depends(get_db)):
    used = db.execute(
        text("SELECT COUNT(*) FROM rental_contracts WHERE plan_id = :id"),
        {"id": plan_id},
    ).scalar()
    if int(used or 0) > 0:
        raise HTTPException(
            status_code=409,
            detail={"type": "RENTAL_PLAN_IN_USE", "message": plan_id},
        )
    res = db.execute(text("DELETE FROM rental_plans WHERE id = :id"), {"id": plan_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_PLAN_NOT_FOUND", "message": plan_id})
    return {"ok": True, "deleted": plan_id}


@router.get("/contracts")
def list_rental_contracts(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    locker_id: Optional[str] = Query(None),
    renter_user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    where_sql, params = _build_contract_filters(
        status=status,
        locker_id=locker_id,
        renter_user_id=renter_user_id,
        tenant_id=tenant_id,
    )
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
                   c.next_billing_at, c.renter_user_id, c.slot_label, c.plan_id, c.currency,
                   c.tenant_id, c.auto_renew, c.started_at, c.ends_at
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
    plan = None
    plan_id = crow.get("plan_id")
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


@router.post("/contracts/preview-pricing")
def preview_rental_contract_pricing(body: RentalContractPricingPreviewIn, db: Session = Depends(get_db)):
    """Cotação (regra dinâmica + seguro opcional) antes de criar o contrato."""
    _ensure_locker(db, body.locker_id)
    ctx = resolve_contract_pricing_context(
        db,
        plan_id=body.plan_id,
        locker_id=body.locker_id,
        slot_label=body.slot_label,
        network_id=body.network_id,
        slot_size=body.slot_size,
        billing_cycle=body.billing_cycle,
        amount_cents=body.amount_cents,
        use_dynamic_pricing=body.use_dynamic_pricing,
    )
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail={"type": ctx["error"], "quote": ctx.get("quote")})
    insurance = None
    if body.content_insurance:
        declared = body.declared_value_cents
        if declared is None or declared <= 0:
            raise HTTPException(
                status_code=400,
                detail={"type": "INSURANCE_DECLARED_VALUE_REQUIRED", "message": "declared_value_cents obrigatório"},
            )
        insurance = calculate_content_insurance_premium(declared)
    return {
        "ok": True,
        "pricing": {
            "amount_cents": ctx["amount_cents"],
            "billing_cycle": ctx["billing_cycle"],
            "currency": ctx["currency"],
            "pricing_source": ctx.get("pricing_source"),
            "pricing_rule_code": ctx.get("pricing_rule_code"),
            "quote": ctx.get("quote"),
        },
        "insurance": insurance,
        "total_monthly_cents": int(ctx["amount_cents"]) + int((insurance or {}).get("premium_cents") or 0),
    }


@router.get("/content-insurance")
def list_content_insurance(
    db: Session = Depends(get_db),
    contract_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if contract_id:
        clauses.append("i.contract_id = :cid")
        params["cid"] = contract_id.strip()
    if status:
        clauses.append("i.status = :st")
        params["st"] = status.strip()
    try:
        rows = db.execute(
            text(
                f"""
                SELECT i.*, c.renter_name, c.locker_id, c.slot_label
                FROM rental_content_insurance i
                JOIN rental_contracts c ON c.id = i.contract_id
                WHERE {" AND ".join(clauses)}
                ORDER BY i.created_at DESC
                """
            ),
            params,
        ).mappings().all()
    except Exception:
        return {"items": [], "total": 0}
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
def create_rental_contract(body: RentalContractIn, db: Session = Depends(get_db)):
    _ensure_locker(db, body.locker_id)
    ctx = resolve_contract_pricing_context(
        db,
        plan_id=body.plan_id,
        locker_id=body.locker_id,
        slot_label=body.slot_label,
        network_id=body.network_id,
        slot_size=body.slot_size,
        billing_cycle=body.billing_cycle,
        amount_cents=body.amount_cents,
        use_dynamic_pricing=body.use_dynamic_pricing,
    )
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail={"type": ctx["error"], "quote": ctx.get("quote")})

    amount_cents = int(ctx["amount_cents"])
    billing_cycle = str(ctx["billing_cycle"])
    currency = body.currency or str(ctx.get("currency") or "BRL")
    pricing_rule_code = ctx.get("pricing_rule_code")
    insurance_premium_cents = 0
    insurance_record = None

    if body.content_insurance:
        declared = body.declared_value_cents
        if declared is None or declared <= 0:
            raise HTTPException(
                status_code=400,
                detail={"type": "INSURANCE_DECLARED_VALUE_REQUIRED", "message": "declared_value_cents obrigatório"},
            )
        calc = calculate_content_insurance_premium(declared)
        insurance_premium_cents = int(calc["premium_cents"])

    contract_id = str(uuid.uuid4())
    now = _utc_now()
    _insert_rental_contract_row(
        db,
        {
            "id": contract_id,
            "locker_id": body.locker_id,
            "slot_label": body.slot_label,
            "plan_id": body.plan_id,
            "tenant_id": body.tenant_id,
            "renter_user_id": body.renter_user_id,
            "renter_name": body.renter_name,
            "renter_document": body.renter_document,
            "renter_phone": body.renter_phone,
            "renter_email": body.renter_email,
            "amount_cents": amount_cents,
            "currency": currency,
            "billing_cycle": billing_cycle,
            "next_billing_at": body.next_billing_at,
            "auto_renew": body.auto_renew,
            "status": body.status,
            "started_at": now if body.status == "ACTIVE" else None,
            "pricing_rule_code": pricing_rule_code,
            "insurance_premium_cents": insurance_premium_cents,
            "now": now,
        },
    )
    if body.content_insurance and body.declared_value_cents:
        insurance_record = create_content_insurance(
            db,
            contract_id=contract_id,
            declared_value_cents=int(body.declared_value_cents),
            currency=currency,
        )
    if body.status == "ACTIVE":
        db.execute(
            text(
                """
                UPDATE locker_slots
                SET status = 'RENTED', current_rental_id = :rid, updated_at = :now
                WHERE locker_id = :lid AND slot_label = :slot
                """
            ),
            {"rid": contract_id, "lid": body.locker_id, "slot": body.slot_label, "now": now},
        )
    log_rental_contract_event(
        db,
        contract_id=contract_id,
        event_type="contract.created",
        payload={
            "status": body.status,
            "plan_id": body.plan_id,
            "pricing_source": ctx.get("pricing_source"),
            "pricing_rule_code": pricing_rule_code,
            "content_insurance": bool(body.content_insurance),
        },
        actor="ops",
    )
    db.commit()
    out = get_rental_contract(contract_id, db)
    out["pricing"] = {
        "pricing_source": ctx.get("pricing_source"),
        "pricing_rule_code": pricing_rule_code,
        "quote": ctx.get("quote"),
        "insurance_premium_cents": insurance_premium_cents,
    }
    if insurance_record:
        out["content_insurance"] = insurance_record
    return out


@router.patch("/contracts/{contract_id}")
def update_rental_contract(
    contract_id: str,
    body: RentalContractUpdate,
    db: Session = Depends(get_db),
):
    if not _contract_row(db, contract_id):
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND", "message": contract_id})
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return get_rental_contract(contract_id, db)
    now = _utc_now()
    if fields.get("status") == "ACTIVE":
        fields.setdefault("started_at", now)
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = contract_id
    fields["updated_at"] = now
    db.execute(
        text(f"UPDATE rental_contracts SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    log_rental_contract_event(
        db,
        contract_id=contract_id,
        event_type="contract.updated",
        payload=fields,
        actor="ops",
    )
    db.commit()
    return get_rental_contract(contract_id, db)


@router.post("/contracts/{contract_id}/cancel")
def cancel_rental_contract(
    contract_id: str,
    body: RentalContractCancelIn,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT locker_id, slot_label, status FROM rental_contracts WHERE id = :id"),
        {"id": contract_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND", "message": contract_id})
    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE rental_contracts
            SET status = 'CANCELLED', cancelled_at = :now, cancel_reason = :reason,
                ended_at = :now, updated_at = :now
            WHERE id = :id
            """
        ),
        {"id": contract_id, "now": now, "reason": body.cancel_reason},
    )
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = 'AVAILABLE', current_rental_id = NULL, updated_at = :now
            WHERE locker_id = :lid AND slot_label = :slot AND current_rental_id = :rid
            """
        ),
        {"lid": str(row["locker_id"]), "slot": str(row["slot_label"]), "rid": contract_id, "now": now},
    )
    log_rental_contract_event(
        db,
        contract_id=contract_id,
        event_type="contract.cancelled",
        payload={"reason": body.cancel_reason},
        actor="ops",
    )
    db.commit()
    return get_rental_contract(contract_id, db)


@router.get("/webhooks")
def list_rental_webhooks(
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Query(None),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if tenant_id:
        clauses.append("tenant_id = :tenant_id")
        params["tenant_id"] = tenant_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, tenant_id, url, events_json, active, created_at, updated_at
            FROM rental_webhook_endpoints
            WHERE {" AND ".join(clauses)}
            ORDER BY tenant_id, created_at DESC
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = _serialize_row(r)
        try:
            item["events"] = json.loads(r.get("events_json") or "[]")
        except json.JSONDecodeError:
            item["events"] = []
        item.pop("events_json", None)
        items.append(item)
    return {"items": items, "total": len(items)}


@router.put("/webhooks/{tenant_id}")
def upsert_rental_webhook(tenant_id: str, body: RentalWebhookIn, db: Session = Depends(get_db)):
    if tenant_id.strip() != body.tenant_id.strip():
        raise HTTPException(status_code=400, detail={"type": "TENANT_MISMATCH"})
    secret = body.secret or secrets.token_urlsafe(24)
    now = _utc_now()
    existing = db.execute(
        text("SELECT id FROM rental_webhook_endpoints WHERE tenant_id = :t LIMIT 1"),
        {"t": tenant_id},
    ).mappings().first()
    events_json = json.dumps(body.events)
    if existing:
        db.execute(
            text(
                """
                UPDATE rental_webhook_endpoints
                SET url = :url, secret_hash = :secret_hash, secret_key = :secret_key,
                    events_json = :events_json, active = :active, updated_at = :now
                WHERE tenant_id = :tenant_id
                """
            ),
            {
                "tenant_id": tenant_id,
                "url": body.url,
                "secret_hash": _hash_secret(secret),
                "secret_key": secret,
                "events_json": events_json,
                "active": body.active,
                "now": now,
            },
        )
        endpoint_id = str(existing["id"])
    else:
        endpoint_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO rental_webhook_endpoints (
                    id, tenant_id, url, secret_hash, secret_key, events_json, active, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :url, :secret_hash, :secret_key, :events_json, :active, :now, :now
                )
                """
            ),
            {
                "id": endpoint_id,
                "tenant_id": tenant_id,
                "url": body.url,
                "secret_hash": _hash_secret(secret),
                "secret_key": secret,
                "events_json": events_json,
                "active": body.active,
                "now": now,
            },
        )
    db.commit()
    return {
        "id": endpoint_id,
        "tenant_id": tenant_id,
        "url": body.url,
        "events": body.events,
        "active": body.active,
        "webhook_secret": secret,
    }


@router.patch("/webhooks/{endpoint_id}")
def patch_rental_webhook(endpoint_id: str, body: RentalWebhookUpdate, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id FROM rental_webhook_endpoints WHERE id = :id"),
        {"id": endpoint_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_WEBHOOK_NOT_FOUND", "message": endpoint_id})
    fields: dict[str, Any] = {}
    if body.url is not None:
        fields["url"] = body.url
    if body.secret is not None:
        fields["secret_hash"] = _hash_secret(body.secret)
        fields["secret_key"] = body.secret
    if body.events is not None:
        fields["events_json"] = json.dumps(body.events)
    if body.active is not None:
        fields["active"] = body.active
    if not fields:
        return {"ok": True}
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = endpoint_id
    fields["updated_at"] = _utc_now()
    db.execute(
        text(f"UPDATE rental_webhook_endpoints SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    db.commit()
    return {"ok": True, "id": endpoint_id}


@router.get("/api-keys")
def list_rental_api_keys(
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Query(None),
    include_revoked: bool = Query(False),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if tenant_id:
        clauses.append("tenant_id = :tenant_id")
        params["tenant_id"] = tenant_id.strip()
    if not include_revoked:
        clauses.append("revoked_at IS NULL")
    rows = db.execute(
        text(
            f"""
            SELECT id, tenant_id, key_prefix, label, scopes_json, expires_at, last_used_at,
                   revoked_at, created_at
            FROM rental_api_keys
            WHERE {" AND ".join(clauses)}
            ORDER BY created_at DESC
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = _serialize_row(r)
        try:
            item["scopes"] = json.loads(r.get("scopes_json") or "[]")
        except json.JSONDecodeError:
            item["scopes"] = []
        item.pop("scopes_json", None)
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/api-keys/{tenant_id}/rotate")
def rotate_rental_api_key(
    tenant_id: str,
    label: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    now = _utc_now()
    db.execute(
        text("UPDATE rental_api_keys SET revoked_at = :now WHERE tenant_id = :t AND revoked_at IS NULL"),
        {"t": tenant_id, "now": now},
    )
    raw, prefix, key_hash = _new_api_key()
    key_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_api_keys (
                id, tenant_id, key_prefix, key_hash, label, scopes_json, created_at
            ) VALUES (
                :id, :tenant_id, :prefix, :key_hash, :label, :scopes, :now
            )
            """
        ),
        {
            "id": key_id,
            "tenant_id": tenant_id,
            "prefix": prefix,
            "key_hash": key_hash,
            "label": label or "rotated",
            "scopes": json.dumps(["rentals:read", "rentals:write", "rentals:webhook"]),
            "now": now,
        },
    )
    db.commit()
    return {"id": key_id, "tenant_id": tenant_id, "key_prefix": prefix, "api_key": raw}


from app.routers import rentals_advanced, rentals_extended, rentals_premium  # noqa: E402

router.include_router(rentals_extended.router)
router.include_router(rentals_premium.router)
router.include_router(rentals_advanced.router)
