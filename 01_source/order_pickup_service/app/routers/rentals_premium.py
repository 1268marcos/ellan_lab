"""RENTAL premium: onboarding KYB, SLA breaches, settlements, capacity, disputes, renewals."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.rentals_premium import (
    RentalDisputeIn,
    RentalOnboardingUpdate,
    RentalRenewalOfferIn,
    RentalSettlementBatchIn,
    RentalSlaBreachIn,
    RentalSlaBreachUpdate,
)
from app.routers.rental_ops_common import serialize_row as _serialize_row
from app.routers.rental_ops_common import utc_now as _utc_now

router = APIRouter(tags=["rentals-ops-premium"])


@router.get("/analytics/premium-summary")
def rental_premium_summary(db: Session = Depends(get_db)):
    """KPIs das funcionalidades premium (onboarding, breaches, settlements, etc.)."""
    def _count(table: str, where: str = "1=1") -> int:
        try:
            return int(
                db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where}")).scalar() or 0
            )
        except Exception:
            return 0

    avg_util_f = 0.0
    try:
        avg_util = db.execute(
            text("SELECT COALESCE(AVG(utilization_pct), 0) FROM rental_capacity_snapshots")
        ).scalar()
        avg_util_f = round(float(avg_util or 0), 2)
    except Exception:
        pass

    return {
        "ok": True,
        "summary": {
            "onboarding_total": _count("rental_network_onboarding"),
            "onboarding_live": _count("rental_network_onboarding", "status = 'LIVE'"),
            "open_sla_breaches": _count("rental_sla_breach_incidents", "status = 'OPEN'"),
            "settlements_pending": _count("rental_settlement_batches", "status IN ('DRAFT', 'APPROVED')"),
            "open_disputes": _count("rental_contract_disputes", "status IN ('OPEN', 'UNDER_REVIEW')"),
            "renewal_offers_pending": _count("rental_renewal_offers", "status = 'PENDING'"),
            "avg_utilization_pct": avg_util_f,
        },
    }


@router.get("/analytics/network-health")
def rental_network_health(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Score composto por rede: onboarding + utilização + breaches abertos."""
    rows = db.execute(
        text(
            """
            SELECT n.id, n.code, n.name,
                   o.status AS onboarding_status,
                   o.compliance_score,
                   (
                       SELECT utilization_pct FROM rental_capacity_snapshots
                       WHERE network_id = n.id
                       ORDER BY snapshot_date DESC LIMIT 1
                   ) AS latest_utilization_pct,
                   (
                       SELECT COUNT(*) FROM rental_sla_breach_incidents
                       WHERE network_id = n.id AND status = 'OPEN'
                   ) AS open_breaches
            FROM rental_networks n
            LEFT JOIN rental_network_onboarding o ON o.network_id = n.id
            WHERE n.active = TRUE
            ORDER BY n.name
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    items = []
    for r in rows:
        score = 70.0
        cs = r.get("compliance_score")
        if cs is not None:
            score += float(cs) * 0.2
        util = float(r.get("latest_utilization_pct") or 0)
        if 40 <= util <= 85:
            score += 5
        score -= int(r.get("open_breaches") or 0) * 8
        if r.get("onboarding_status") == "LIVE":
            score += 10
        items.append({
            **_serialize_row(r),
            "health_score": round(max(0, min(100, score)), 1),
        })
    return {"items": items, "total": len(items)}


@router.get("/onboarding")
def list_network_onboarding(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("o.status = :status")
        params["status"] = status.strip()
    rows = db.execute(
        text(
            f"""
            SELECT o.*, n.code AS network_code, n.name AS network_name
            FROM rental_network_onboarding o
            JOIN rental_networks n ON n.id = o.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY o.updated_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.patch("/onboarding/{network_id}")
def update_network_onboarding(network_id: str, body: RentalOnboardingUpdate, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, status FROM rental_network_onboarding WHERE network_id = :n"),
        {"n": network_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "ONBOARDING_NOT_FOUND"})
    now = _utc_now()
    fields = body.model_dump(exclude_unset=True)
    if body.status == "KYC_SUBMITTED" and "submitted_at" not in fields:
        fields["submitted_at"] = now
    if body.status == "APPROVED":
        fields.setdefault("approved_at", now)
    if body.status == "LIVE":
        fields.setdefault("live_at", now)
    if not fields:
        return {"ok": True}
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    db.execute(
        text(f"UPDATE rental_network_onboarding SET {sets}, updated_at = :now WHERE network_id = :nid"),
        {**fields, "now": now, "nid": network_id},
    )
    db.commit()
    return {"ok": True, "network_id": network_id}


@router.get("/sla-breaches")
def list_sla_breaches(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("b.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT b.*, n.code AS network_code
            FROM rental_sla_breach_incidents b
            JOIN rental_networks n ON n.id = b.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY b.detected_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/sla-breaches", status_code=status.HTTP_201_CREATED)
def create_sla_breach(body: RentalSlaBreachIn, db: Session = Depends(get_db)):
    bid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_sla_breach_incidents (
                id, network_id, sla_policy_id, contract_id, metric_code,
                target_value, measured_value, severity, status, penalty_cents,
                currency, detected_at, created_at
            ) VALUES (
                :id, :nid, :sid, :cid, :mc, :tv, :mv, :sev, 'OPEN', :pen,
                :cur, :now, :now
            )
            """
        ),
        {
            "id": bid,
            "nid": body.network_id,
            "sid": body.sla_policy_id,
            "cid": body.contract_id,
            "mc": body.metric_code,
            "tv": float(body.target_value),
            "mv": float(body.measured_value),
            "sev": body.severity,
            "pen": body.penalty_cents,
            "cur": body.currency,
            "now": now,
        },
    )
    db.commit()
    return {"id": bid, **body.model_dump(mode="json")}


@router.patch("/sla-breaches/{breach_id}")
def update_sla_breach(breach_id: str, body: RentalSlaBreachUpdate, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_sla_breach_incidents WHERE id = :id"), {"id": breach_id}).first():
        raise HTTPException(status_code=404, detail={"type": "SLA_BREACH_NOT_FOUND"})
    now = _utc_now()
    fields = body.model_dump(exclude_unset=True)
    if body.status in ("ACKNOWLEDGED", "RESOLVED", "CREDITED"):
        if body.status == "ACKNOWLEDGED":
            fields.setdefault("acknowledged_at", now)
        else:
            fields.setdefault("resolved_at", now)
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    db.execute(
        text(f"UPDATE rental_sla_breach_incidents SET {sets} WHERE id = :id"),
        {**fields, "id": breach_id},
    )
    db.commit()
    return {"ok": True, "id": breach_id}


@router.get("/settlements")
def list_settlements(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("s.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT s.*, o.legal_name AS operator_name, o.operator_code
            FROM rental_settlement_batches s
            JOIN rental_operators o ON o.id = s.operator_id
            WHERE {" AND ".join(clauses)}
            ORDER BY s.period_end DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/settlements", status_code=status.HTTP_201_CREATED)
def create_settlement(body: RentalSettlementBatchIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_operators WHERE id = :id"), {"id": body.operator_id}).first():
        raise HTTPException(status_code=404, detail={"type": "OPERATOR_NOT_FOUND"})
    net = body.gross_cents - body.commission_cents + body.adjustments_cents
    sid = str(uuid.uuid4())
    code = f"STL-{uuid.uuid4().hex[:8].upper()}"
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_settlement_batches (
                id, operator_id, batch_code, period_start, period_end,
                gross_cents, commission_cents, adjustments_cents, net_cents,
                currency, status, created_at, updated_at
            ) VALUES (
                :id, :oid, :code, :start, :end, :gross, :comm, :adj, :net,
                :cur, 'DRAFT', :now, :now
            )
            """
        ),
        {
            "id": sid,
            "oid": body.operator_id,
            "code": code,
            "start": body.period_start,
            "end": body.period_end,
            "gross": body.gross_cents,
            "comm": body.commission_cents,
            "adj": body.adjustments_cents,
            "net": net,
            "cur": body.currency,
            "now": now,
        },
    )
    db.commit()
    return {"id": sid, "batch_code": code, "net_cents": net}


@router.post("/settlements/{batch_id}/approve")
def approve_settlement(batch_id: str, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
            UPDATE rental_settlement_batches
            SET status = 'APPROVED', approved_by = 'ops', updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND status = 'DRAFT'
            """
        ),
        {"id": batch_id},
    )
    db.commit()
    return {"ok": True, "id": batch_id}


@router.get("/capacity")
def list_capacity_snapshots(
    db: Session = Depends(get_db),
    network_id: Optional[str] = Query(None),
    days: int = Query(14, ge=1, le=90),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit_rows": days * 50}
    if network_id:
        clauses.append("c.network_id = :nid")
        params["nid"] = network_id
    rows = db.execute(
        text(
            f"""
            SELECT c.*, n.code AS network_code, n.name AS network_name
            FROM rental_capacity_snapshots c
            JOIN rental_networks n ON n.id = c.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY c.snapshot_date DESC, n.code
            LIMIT :limit_rows
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.get("/disputes")
def list_disputes(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("d.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT d.*, c.renter_name, c.locker_id
            FROM rental_contract_disputes d
            JOIN rental_contracts c ON c.id = d.contract_id
            WHERE {" AND ".join(clauses)}
            ORDER BY d.opened_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/disputes", status_code=status.HTTP_201_CREATED)
def create_dispute(body: RentalDisputeIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": body.contract_id}).first():
        raise HTTPException(status_code=404, detail={"type": "CONTRACT_NOT_FOUND"})
    did = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_contract_disputes (
                id, contract_id, dispute_type, amount_cents, currency, status, reason, opened_at, created_at
            ) VALUES (:id, :cid, :dt, :amt, :cur, 'OPEN', :reason, :now, :now)
            """
        ),
        {
            "id": did,
            "cid": body.contract_id,
            "dt": body.dispute_type,
            "amt": body.amount_cents,
            "cur": body.currency,
            "reason": body.reason,
            "now": now,
        },
    )
    db.commit()
    return {"id": did, **body.model_dump(mode="json")}


@router.get("/renewal-offers")
def list_renewal_offers(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("r.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT r.*, c.renter_name, c.status AS contract_status
            FROM rental_renewal_offers r
            JOIN rental_contracts c ON c.id = r.contract_id
            WHERE {" AND ".join(clauses)}
            ORDER BY r.valid_until ASC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/renewal-offers", status_code=status.HTTP_201_CREATED)
def create_renewal_offer(body: RentalRenewalOfferIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": body.contract_id}).first():
        raise HTTPException(status_code=404, detail={"type": "CONTRACT_NOT_FOUND"})
    rid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_renewal_offers (
                id, contract_id, offer_amount_cents, currency, billing_cycle,
                valid_until, status, auto_renew, sent_at, created_at
            ) VALUES (
                :id, :cid, :amt, :cur, :cycle, :valid, 'PENDING', :auto, :now, :now
            )
            """
        ),
        {
            "id": rid,
            "cid": body.contract_id,
            "amt": body.offer_amount_cents,
            "cur": body.currency,
            "cycle": body.billing_cycle,
            "valid": body.valid_until,
            "auto": body.auto_renew,
            "now": now,
        },
    )
    db.commit()
    return {"id": rid, **body.model_dump(mode="json")}


@router.post("/renewal-offers/{offer_id}/accept")
def accept_renewal_offer(offer_id: str, db: Session = Depends(get_db)):
    offer = db.execute(
        text("SELECT contract_id, offer_amount_cents, billing_cycle FROM rental_renewal_offers WHERE id = :id"),
        {"id": offer_id},
    ).mappings().first()
    if not offer:
        raise HTTPException(status_code=404, detail={"type": "RENEWAL_OFFER_NOT_FOUND"})
    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE rental_renewal_offers
            SET status = 'ACCEPTED', responded_at = :now
            WHERE id = :id
            """
        ),
        {"id": offer_id, "now": now},
    )
    db.execute(
        text(
            """
            UPDATE rental_contracts
            SET amount_cents = :amt, billing_cycle = :cycle, updated_at = :now
            WHERE id = :cid
            """
        ),
        {
            "amt": int(offer["offer_amount_cents"]),
            "cycle": str(offer["billing_cycle"]),
            "cid": str(offer["contract_id"]),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "offer_id": offer_id, "contract_id": str(offer["contract_id"])}
