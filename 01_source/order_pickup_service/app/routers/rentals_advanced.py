"""RENTAL avançado: acesso, caução, bloqueios, pricing, dunning, transferências."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.rentals_advanced import (
    RentalAccessPassIssueIn,
    RentalDepositHoldIn,
    RentalPricingRuleIn,
    RentalQuoteIn,
    RentalSlotBlockIn,
    RentalTransferRequestIn,
)
from app.routers.rental_ops_common import serialize_row as _serialize_row
from app.routers.rental_ops_common import utc_now as _utc_now
from app.services.rental_events import log_rental_contract_event
from app.services.rental_late_fees import apply_automatic_late_fees
from app.services.rental_pricing import resolve_rental_quote

router = APIRouter(tags=["rentals-ops-advanced"])


def _hash_code(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/contracts/{contract_id}/activate")
def activate_rental_contract(contract_id: str, db: Session = Depends(get_db)):
    """Ativa contrato PENDING e reserva o slot."""
    row = db.execute(
        text("SELECT locker_id, slot_label, status FROM rental_contracts WHERE id = :id"),
        {"id": contract_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    if str(row["status"]) == "ACTIVE":
        return {"ok": True, "contract_id": contract_id, "status": "ACTIVE"}
    if str(row["status"]) not in ("PENDING", "SUSPENDED"):
        raise HTTPException(
            status_code=409,
            detail={"type": "INVALID_STATUS", "message": f"Cannot activate from {row['status']}"},
        )
    block = db.execute(
        text(
            """
            SELECT id FROM rental_slot_blocks
            WHERE locker_id = :lid AND slot_label = :slot AND active = TRUE
              AND starts_at <= CURRENT_TIMESTAMP AND ends_at >= CURRENT_TIMESTAMP
            LIMIT 1
            """
        ),
        {"lid": row["locker_id"], "slot": row["slot_label"]},
    ).mappings().first()
    if block:
        raise HTTPException(status_code=409, detail={"type": "SLOT_BLOCKED", "message": "Slot em manutenção"})

    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE rental_contracts
            SET status = 'ACTIVE', started_at = COALESCE(started_at, :now), updated_at = :now
            WHERE id = :id
            """
        ),
        {"id": contract_id, "now": now},
    )
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = 'RENTED', current_rental_id = :rid, updated_at = :now
            WHERE locker_id = :lid AND slot_label = :slot
            """
        ),
        {"rid": contract_id, "lid": row["locker_id"], "slot": row["slot_label"], "now": now},
    )
    log_rental_contract_event(
        db, contract_id=contract_id, event_type="contract.activated", payload={}, actor="ops"
    )
    db.commit()
    return {"ok": True, "contract_id": contract_id, "status": "ACTIVE"}


@router.post("/contracts/{contract_id}/access-passes", status_code=status.HTTP_201_CREATED)
def issue_access_pass(contract_id: str, body: RentalAccessPassIssueIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": contract_id}).first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    raw = f"{secrets.randbelow(900000) + 100000:06d}" if body.pass_type == "PIN" else secrets.token_urlsafe(12)
    now = _utc_now()
    valid_until = now + timedelta(hours=body.valid_hours)
    pid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_access_passes (
                id, contract_id, pass_type, pass_code_hash, pass_hint,
                valid_from, valid_until, max_uses, status, created_at
            ) VALUES (
                :id, :cid, :ptype, :hash, :hint, :now, :until, :max, 'ACTIVE', :now
            )
            """
        ),
        {
            "id": pid,
            "cid": contract_id,
            "ptype": body.pass_type,
            "hash": _hash_code(raw),
            "hint": raw[:2] + "****",
            "now": now,
            "until": valid_until,
            "max": body.max_uses,
        },
    )
    log_rental_contract_event(
        db,
        contract_id=contract_id,
        event_type="access_pass.issued",
        payload={"pass_id": pid, "pass_type": body.pass_type},
        actor="ops",
    )
    db.commit()
    return {
        "id": pid,
        "contract_id": contract_id,
        "pass_type": body.pass_type,
        "pass_code": raw,
        "valid_until": valid_until.isoformat(),
    }


@router.get("/access-passes")
def list_access_passes(db: Session = Depends(get_db), contract_id: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if contract_id:
        clauses.append("p.contract_id = :cid")
        params["cid"] = contract_id
    rows = db.execute(
        text(
            f"""
            SELECT p.id, p.contract_id, p.pass_type, p.pass_hint, p.valid_from, p.valid_until,
                   p.max_uses, p.use_count, p.status, p.created_at
            FROM rental_access_passes p
            WHERE {" AND ".join(clauses)}
            ORDER BY p.created_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/access-passes/{pass_id}/revoke")
def revoke_access_pass(pass_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE rental_access_passes
            SET status = 'REVOKED', revoked_at = :now
            WHERE id = :id AND status = 'ACTIVE'
            """
        ),
        {"id": pass_id, "now": now},
    )
    db.commit()
    return {"ok": True, "id": pass_id}


@router.get("/deposits")
def list_deposit_holds(db: Session = Depends(get_db), contract_id: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if contract_id:
        clauses.append("d.contract_id = :cid")
        params["cid"] = contract_id
    rows = db.execute(
        text(
            f"""
            SELECT d.*, c.renter_name
            FROM rental_deposit_holds d
            JOIN rental_contracts c ON c.id = d.contract_id
            WHERE {" AND ".join(clauses)}
            ORDER BY d.held_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/deposits", status_code=status.HTTP_201_CREATED)
def create_deposit_hold(body: RentalDepositHoldIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": body.contract_id}).first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    did = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_deposit_holds (
                id, contract_id, amount_cents, currency, status, hold_reason,
                payment_ref, held_at, created_at
            ) VALUES (
                :id, :cid, :amt, :cur, 'HELD', :reason, :pref, :now, :now
            )
            """
        ),
        {
            "id": did,
            "cid": body.contract_id,
            "amt": body.amount_cents,
            "cur": body.currency,
            "reason": body.hold_reason,
            "pref": body.payment_ref,
            "now": now,
        },
    )
    db.commit()
    return {"id": did, **body.model_dump()}


@router.post("/deposits/{deposit_id}/release")
def release_deposit(deposit_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE rental_deposit_holds
            SET status = 'RELEASED', released_at = :now
            WHERE id = :id AND status = 'HELD'
            """
        ),
        {"id": deposit_id, "now": now},
    )
    db.commit()
    return {"ok": True, "id": deposit_id, "status": "RELEASED"}


@router.get("/slot-blocks")
def list_slot_blocks(db: Session = Depends(get_db), locker_id: Optional[str] = Query(None), active_only: bool = True):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if locker_id:
        clauses.append("locker_id = :lid")
        params["lid"] = locker_id
    if active_only:
        clauses.append("active = TRUE AND ends_at >= CURRENT_TIMESTAMP")
    rows = db.execute(
        text(
            f"""
            SELECT * FROM rental_slot_blocks
            WHERE {" AND ".join(clauses)}
            ORDER BY starts_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/slot-blocks", status_code=status.HTTP_201_CREATED)
def create_slot_block(body: RentalSlotBlockIn, db: Session = Depends(get_db)):
    if body.ends_at <= body.starts_at:
        raise HTTPException(status_code=400, detail={"type": "INVALID_WINDOW"})
    bid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_slot_blocks (
                id, locker_id, slot_label, block_type, reason, starts_at, ends_at, created_at
            ) VALUES (
                :id, :lid, :slot, :bt, :reason, :start, :end, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": bid,
            "lid": body.locker_id,
            "slot": body.slot_label,
            "bt": body.block_type,
            "reason": body.reason,
            "start": body.starts_at,
            "end": body.ends_at,
        },
    )
    db.commit()
    return {"id": bid, **body.model_dump(mode="json")}


@router.get("/pricing-rules")
def list_pricing_rules(db: Session = Depends(get_db), network_id: Optional[str] = Query(None)):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if network_id:
        clauses.append("(network_id = :nid OR network_id IS NULL)")
        params["nid"] = network_id
    rows = db.execute(
        text(
            f"""
            SELECT r.*, n.code AS network_code
            FROM rental_pricing_rules r
            LEFT JOIN rental_networks n ON n.id = r.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY r.priority ASC, r.code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/pricing-rules", status_code=status.HTTP_201_CREATED)
def create_pricing_rule(body: RentalPricingRuleIn, db: Session = Depends(get_db)):
    rid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_pricing_rules (
                id, code, name, network_id, slot_size, billing_cycle,
                base_amount_cents, surge_multiplier, valid_from, valid_until,
                priority, active, created_at
            ) VALUES (
                :id, :code, :name, :nid, :size, :cycle, :base, :surge,
                :vf, :vu, :pri, :active, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": rid,
            "code": body.code.strip().upper(),
            "name": body.name,
            "nid": body.network_id,
            "size": body.slot_size,
            "cycle": body.billing_cycle,
            "base": body.base_amount_cents,
            "surge": float(body.surge_multiplier),
            "vf": body.valid_from,
            "vu": body.valid_until,
            "pri": body.priority,
            "active": body.active,
        },
    )
    db.commit()
    return {"id": rid, **body.model_dump(mode="json")}


@router.post("/pricing/quote")
def rental_price_quote(body: RentalQuoteIn, db: Session = Depends(get_db)):
    """Cotação dinâmica com base em regras cadastradas."""
    quote = resolve_rental_quote(
        db,
        network_id=body.network_id,
        slot_size=body.slot_size,
        billing_cycle=body.billing_cycle or "MONTHLY",
        at=body.at,
    )
    return {"ok": True, **quote, "rule_code": quote.get("rule_code"), "rule_name": quote.get("rule_name")}


@router.get("/dunning")
def list_dunning_cases(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("d.status = :st")
        params["st"] = status
    rows = db.execute(
        text(
            f"""
            SELECT d.*, c.renter_name, c.locker_id
            FROM rental_dunning_cases d
            JOIN rental_contracts c ON c.id = d.contract_id
            WHERE {" AND ".join(clauses)}
            ORDER BY d.next_action_at ASC, d.created_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/dunning/scan")
def scan_dunning(db: Session = Depends(get_db)):
    """Aplica multas automáticas e abre casos de cobrança para faturas OVERDUE sem caso aberto."""
    late_fees = apply_automatic_late_fees(db)
    rows = db.execute(
        text(
            """
            SELECT i.id AS invoice_id, i.contract_id, i.amount_cents, i.currency
            FROM rental_billing_invoices i
            WHERE i.status = 'OVERDUE'
              AND NOT EXISTS (
                  SELECT 1 FROM rental_dunning_cases d
                  WHERE d.invoice_id = i.id AND d.status = 'OPEN'
              )
            """
        )
    ).mappings().all()
    created = 0
    now = _utc_now()
    for r in rows:
        db.execute(
            text(
                """
                INSERT INTO rental_dunning_cases (
                    id, contract_id, invoice_id, stage, amount_due_cents, currency,
                    status, next_action_at, created_at, updated_at
                ) VALUES (
                    :id, :cid, :iid, 'REMINDER_1', :amt, :cur, 'OPEN', :next, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": str(r["contract_id"]),
                "iid": str(r["invoice_id"]),
                "amt": int(r["amount_cents"]),
                "cur": str(r["currency"]),
                "next": now + timedelta(days=3),
                "now": now,
            },
        )
        created += 1
    db.commit()
    return {"ok": True, "cases_created": created, "late_fees": late_fees}


@router.get("/transfers")
def list_transfer_requests(db: Session = Depends(get_db), status: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("t.status = :st")
        params["st"] = status
    rows = db.execute(
        text(
            f"""
            SELECT t.*, c.renter_name
            FROM rental_transfer_requests t
            JOIN rental_contracts c ON c.id = t.contract_id
            WHERE {" AND ".join(clauses)}
            ORDER BY t.created_at DESC
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/transfers", status_code=status.HTTP_201_CREATED)
def create_transfer_request(body: RentalTransferRequestIn, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT locker_id, slot_label, status FROM rental_contracts WHERE id = :id"),
        {"id": body.contract_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    tid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_transfer_requests (
                id, contract_id, from_locker_id, from_slot_label,
                to_locker_id, to_slot_label, status, requested_by, created_at
            ) VALUES (
                :id, :cid, :fl, :fs, :tl, :ts, 'REQUESTED', :by, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": tid,
            "cid": body.contract_id,
            "fl": row["locker_id"],
            "fs": row["slot_label"],
            "tl": body.to_locker_id,
            "ts": body.to_slot_label,
            "by": body.requested_by,
        },
    )
    log_rental_contract_event(
        db,
        contract_id=body.contract_id,
        event_type="transfer.requested",
        payload={"transfer_id": tid, "to_locker_id": body.to_locker_id},
        actor=body.requested_by,
    )
    db.commit()
    return {"id": tid, **body.model_dump()}


@router.post("/transfers/{transfer_id}/complete")
def complete_transfer(transfer_id: str, db: Session = Depends(get_db)):
    t = db.execute(
        text("SELECT * FROM rental_transfer_requests WHERE id = :id"),
        {"id": transfer_id},
    ).mappings().first()
    if not t:
        raise HTTPException(status_code=404, detail={"type": "TRANSFER_NOT_FOUND"})
    if str(t["status"]) not in ("REQUESTED", "APPROVED"):
        raise HTTPException(status_code=409, detail={"type": "INVALID_TRANSFER_STATUS"})
    now = _utc_now()
    cid = str(t["contract_id"])
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = 'AVAILABLE', current_rental_id = NULL, updated_at = :now
            WHERE locker_id = :fl AND slot_label = :fs
            """
        ),
        {"fl": t["from_locker_id"], "fs": t["from_slot_label"], "now": now},
    )
    db.execute(
        text(
            """
            UPDATE rental_contracts
            SET locker_id = :tl, slot_label = :ts, updated_at = :now
            WHERE id = :cid
            """
        ),
        {"tl": t["to_locker_id"], "ts": t["to_slot_label"], "cid": cid, "now": now},
    )
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = 'RENTED', current_rental_id = :cid, updated_at = :now
            WHERE locker_id = :tl AND slot_label = :ts
            """
        ),
        {"cid": cid, "tl": t["to_locker_id"], "ts": t["to_slot_label"], "now": now},
    )
    db.execute(
        text(
            """
            UPDATE rental_transfer_requests
            SET status = 'COMPLETED', completed_at = :now
            WHERE id = :id
            """
        ),
        {"id": transfer_id, "now": now},
    )
    log_rental_contract_event(
        db,
        contract_id=cid,
        event_type="transfer.completed",
        payload={"transfer_id": transfer_id},
        actor="ops",
    )
    db.commit()
    return {"ok": True, "transfer_id": transfer_id, "contract_id": cid}
