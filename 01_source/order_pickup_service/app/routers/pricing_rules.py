from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.schemas.pricing_rules import (
    PricingRuleCreateIn,
    PricingRuleListOut,
    PricingRuleOut,
    PricingRulePatchIn,
)

_OPS = {"admin_operacao", "auditoria", "suporte"}

router = APIRouter(
    prefix="/pricing",
    tags=["pricing-rules"],
    dependencies=[Depends(require_user_roles(allowed_roles=_OPS))],
)


def _row(r: dict) -> PricingRuleOut:
    meta = r.get("metadata") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta) if meta.strip() else {}
        except json.JSONDecodeError:
            meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return PricingRuleOut(
        id=str(r["id"]),
        region=r.get("region"),
        locker_id=r.get("locker_id"),
        product_category=r.get("product_category"),
        valid_from=r["valid_from"],
        valid_until=r.get("valid_until"),
        base_amount_cents=int(r["base_amount_cents"]),
        discount_pct=float(r.get("discount_pct") or 0),
        min_amount_cents=(int(r["min_amount_cents"]) if r.get("min_amount_cents") is not None else None),
        max_amount_cents=(int(r["max_amount_cents"]) if r.get("max_amount_cents") is not None else None),
        is_active=bool(r.get("is_active", True)),
        metadata_json=meta,
        created_at=r["created_at"],
    )


@router.get("/rules", response_model=PricingRuleListOut)
def list_pricing_rules(
    db: Session = Depends(get_db),
    region: str | None = None,
    locker_id: str | None = None,
    product_category: str | None = None,
    is_active: bool | None = None,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    cond, p = ["1=1"], {}
    if region is not None:
        cond.append("region = :region")
        p["region"] = region[:20]
    if locker_id is not None:
        cond.append("locker_id = :locker_id")
        p["locker_id"] = locker_id[:36]
    if product_category is not None:
        cond.append("product_category = :product_category")
        p["product_category"] = product_category[:64]
    if is_active is not None:
        cond.append("is_active = :is_active")
        p["is_active"] = is_active
    p["limit"], p["offset"] = limit, offset
    sql = f"""
        SELECT id, region, locker_id, product_category, valid_from, valid_until,
               base_amount_cents, discount_pct, min_amount_cents, max_amount_cents,
               is_active, metadata, created_at
        FROM pricing_rules WHERE {' AND '.join(cond)}
        ORDER BY valid_from DESC NULLS LAST, id
        LIMIT :limit OFFSET :offset
    """
    rows = [dict(x) for x in db.execute(text(sql), p).mappings().all()]
    return PricingRuleListOut(items=[_row(x) for x in rows])


@router.post("/rules", response_model=PricingRuleOut)
def create_pricing_rule(payload: PricingRuleCreateIn, db: Session = Depends(get_db)):
    rid = str(uuid4())
    meta = json.dumps(payload.metadata_json or {})
    db.execute(
        text(
            """
            INSERT INTO pricing_rules (
              id, region, locker_id, product_category, valid_from, valid_until,
              base_amount_cents, discount_pct, min_amount_cents, max_amount_cents, is_active, metadata
            ) VALUES (
              :id, :region, :locker_id, :product_category, :valid_from, :valid_until,
              :base_amount_cents, :discount_pct, :min_amount_cents, :max_amount_cents, :is_active, CAST(:metadata AS jsonb)
            )
            """
        ),
        {
            "id": rid,
            "region": payload.region,
            "locker_id": payload.locker_id,
            "product_category": payload.product_category,
            "valid_from": payload.valid_from,
            "valid_until": payload.valid_until,
            "base_amount_cents": payload.base_amount_cents,
            "discount_pct": payload.discount_pct,
            "min_amount_cents": payload.min_amount_cents,
            "max_amount_cents": payload.max_amount_cents,
            "is_active": payload.is_active,
            "metadata": meta,
        },
    )
    db.commit()
    row = db.execute(
        text(
            "SELECT id, region, locker_id, product_category, valid_from, valid_until, base_amount_cents, "
            "discount_pct, min_amount_cents, max_amount_cents, is_active, metadata, created_at "
            "FROM pricing_rules WHERE id = :id"
        ),
        {"id": rid},
    ).mappings().first()
    if not row:
        raise HTTPException(500, detail="create_failed")
    return _row(dict(row))


@router.patch("/rules/{rule_id}", response_model=PricingRuleOut)
def patch_pricing_rule(rule_id: str, payload: PricingRulePatchIn, db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM pricing_rules WHERE id = :id LIMIT 1"), {"id": rule_id}).scalar()
    if not exists:
        raise HTTPException(404, detail="rule_not_found")
    raw = payload.model_dump(exclude_unset=True)
    if not raw:
        raise HTTPException(400, detail="empty_patch")
    if "metadata_json" in raw:
        raw["metadata"] = json.dumps(raw.pop("metadata_json") or {})
    sets, bind = [], {"id": rule_id}
    colmap = {
        "region": "region",
        "locker_id": "locker_id",
        "product_category": "product_category",
        "valid_from": "valid_from",
        "valid_until": "valid_until",
        "base_amount_cents": "base_amount_cents",
        "discount_pct": "discount_pct",
        "min_amount_cents": "min_amount_cents",
        "max_amount_cents": "max_amount_cents",
        "is_active": "is_active",
    }
    for k, col in colmap.items():
        if k in raw:
            sets.append(f"{col} = :{k}")
            bind[k] = raw[k]
    if "metadata" in raw:
        sets.append("metadata = CAST(:metadata AS jsonb)")
        bind["metadata"] = raw["metadata"]
    if not sets:
        raise HTTPException(400, detail="empty_patch")
    db.execute(text(f"UPDATE pricing_rules SET {', '.join(sets)} WHERE id = :id"), bind)
    db.commit()
    row = db.execute(
        text(
            "SELECT id, region, locker_id, product_category, valid_from, valid_until, base_amount_cents, "
            "discount_pct, min_amount_cents, max_amount_cents, is_active, metadata, created_at "
            "FROM pricing_rules WHERE id = :id"
        ),
        {"id": rule_id},
    ).mappings().first()
    return _row(dict(row))
