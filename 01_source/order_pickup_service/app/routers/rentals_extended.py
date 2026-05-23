"""OPS estendido: redes mundiais, operadores, faturamento, SLA e analytics rental."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.rentals_extended import (
    RentalBillingInvoiceIn,
    RentalBillingInvoiceUpdate,
    RentalCorridorIn,
    RentalNetworkIn,
    RentalNetworkUpdate,
    RentalOperatorIn,
    RentalOperatorUpdate,
    RentalSlaPolicyIn,
)
from app.routers.rental_ops_common import serialize_row as _serialize_row
from app.routers.rental_ops_common import utc_now as _utc_now

router = APIRouter(tags=["rentals-ops-extended"])


def _json_countries(countries: list[str]) -> str:
    return json.dumps([c.upper()[:2] for c in countries if c])


@router.get("/analytics/summary")
def rental_analytics_summary(db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM rental_plans WHERE active = TRUE) AS active_plans,
                (SELECT COUNT(*) FROM rental_contracts) AS total_contracts,
                (SELECT COUNT(*) FROM rental_contracts WHERE status = 'ACTIVE') AS active_contracts,
                (SELECT COUNT(*) FROM rental_contracts WHERE status = 'OVERDUE') AS overdue_contracts,
                (SELECT COALESCE(SUM(amount_cents), 0) FROM rental_contracts WHERE status = 'ACTIVE') AS mrr_cents,
                (SELECT COUNT(*) FROM rental_networks WHERE active = TRUE) AS active_networks,
                (SELECT COUNT(*) FROM rental_operators WHERE status = 'ACTIVE') AS active_operators,
                (SELECT COUNT(*) FROM rental_billing_invoices WHERE status = 'OVERDUE') AS overdue_invoices,
                (SELECT COALESCE(SUM(amount_cents), 0) FROM rental_billing_invoices WHERE status = 'PAID') AS paid_invoice_cents
            """
        )
    ).mappings().first()
    return {"ok": True, "summary": _serialize_row(row) if row else {}}


@router.get("/network-relations")
def list_rental_network_relations(
    db: Session = Depends(get_db),
    network_id: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
):
    clauses = ["r.active = TRUE"]
    params: dict[str, Any] = {}
    if network_id:
        clauses.append("(r.from_network_id = :nid OR r.to_network_id = :nid)")
        params["nid"] = network_id.strip()
    if relation_type:
        clauses.append("r.relation_type = :rt")
        params["rt"] = relation_type.strip()
    rows = db.execute(
        text(
            f"""
            SELECT r.id, r.from_network_id, r.to_network_id, r.relation_type, r.integration_mode,
                   r.active, r.created_at,
                   fn.code AS from_code, fn.name AS from_name,
                   tn.code AS to_code, tn.name AS to_name
            FROM rental_network_relations r
            JOIN rental_networks fn ON fn.id = r.from_network_id
            JOIN rental_networks tn ON tn.id = r.to_network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY fn.code, tn.code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.get("/networks")
def list_rental_networks(
    db: Session = Depends(get_db),
    network_type: Optional[str] = Query(None),
    market_segment: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if network_type:
        clauses.append("network_type = :network_type")
        params["network_type"] = network_type.strip()
    if market_segment:
        clauses.append("market_segment = :market_segment")
        params["market_segment"] = market_segment.strip()
    if active_only:
        clauses.append("active = TRUE")
    cols = (
        "id, code, name, network_type, hardware_vendor, primary_countries_json, "
        "website_url, active, created_at, updated_at"
    )
    try:
        db.execute(text("SELECT market_segment FROM rental_networks LIMIT 0"))
        cols += ", market_segment, global_player_code"
    except Exception:
        pass
    rows = db.execute(
        text(
            f"""
            SELECT {cols}
            FROM rental_networks
            WHERE {" AND ".join(clauses)}
            ORDER BY name
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = _serialize_row(r)
        try:
            item["primary_countries"] = json.loads(r.get("primary_countries_json") or "[]")
        except json.JSONDecodeError:
            item["primary_countries"] = []
        item.pop("primary_countries_json", None)
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/networks", status_code=status.HTTP_201_CREATED)
def create_rental_network(body: RentalNetworkIn, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT id FROM rental_networks WHERE code = :code"),
        {"code": body.code.strip().upper()},
    ).mappings().first()
    if exists:
        raise HTTPException(status_code=409, detail={"type": "RENTAL_NETWORK_EXISTS", "message": body.code})
    net_id = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_networks (
                id, code, name, network_type, hardware_vendor, primary_countries_json,
                website_url, active, created_at, updated_at
            ) VALUES (
                :id, :code, :name, :network_type, :hardware_vendor, :countries,
                :website_url, :active, :now, :now
            )
            """
        ),
        {
            "id": net_id,
            "code": body.code.strip().upper(),
            "name": body.name,
            "network_type": body.network_type,
            "hardware_vendor": body.hardware_vendor,
            "countries": _json_countries(body.primary_countries),
            "website_url": body.website_url,
            "active": body.active,
            "now": now,
        },
    )
    db.commit()
    return _network_row(db, net_id)


def _network_row(db: Session, net_id: str) -> dict[str, Any]:
    r = db.execute(text("SELECT * FROM rental_networks WHERE id = :id"), {"id": net_id}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail={"type": "RENTAL_NETWORK_NOT_FOUND"})
    item = _serialize_row(r)
    try:
        item["primary_countries"] = json.loads(r.get("primary_countries_json") or "[]")
    except json.JSONDecodeError:
        item["primary_countries"] = []
    return item


@router.patch("/networks/{network_id}")
def update_rental_network(network_id: str, body: RentalNetworkUpdate, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_networks WHERE id = :id"), {"id": network_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_NETWORK_NOT_FOUND", "message": network_id})
    fields = body.model_dump(exclude_unset=True)
    if "primary_countries" in fields:
        fields["primary_countries_json"] = _json_countries(fields.pop("primary_countries") or [])
    if not fields:
        return _network_row(db, network_id)
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = network_id
    fields["updated_at"] = _utc_now()
    db.execute(text(f"UPDATE rental_networks SET {sets}, updated_at = :updated_at WHERE id = :id"), fields)
    db.commit()
    return _network_row(db, network_id)


@router.get("/corridors")
def list_rental_corridors(
    db: Session = Depends(get_db),
    network_id: Optional[str] = Query(None),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if network_id:
        clauses.append("c.network_id = :network_id")
        params["network_id"] = network_id
    rows = db.execute(
        text(
            f"""
            SELECT c.id, c.network_id, n.code AS network_code, n.name AS network_name,
                   c.origin_country, c.destination_country, c.sla_hours, c.currency, c.active, c.created_at
            FROM rental_network_corridors c
            JOIN rental_networks n ON n.id = c.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY n.name, c.origin_country, c.destination_country
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/corridors", status_code=status.HTTP_201_CREATED)
def create_rental_corridor(body: RentalCorridorIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_networks WHERE id = :id"), {"id": body.network_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_NETWORK_NOT_FOUND"})
    cid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_network_corridors (
                id, network_id, origin_country, destination_country, sla_hours, currency, active, created_at
            ) VALUES (
                :id, :network_id, :origin, :dest, :sla_hours, :currency, :active, :now
            )
            """
        ),
        {
            "id": cid,
            "network_id": body.network_id,
            "origin": body.origin_country.upper(),
            "dest": body.destination_country.upper(),
            "sla_hours": body.sla_hours,
            "currency": body.currency,
            "active": body.active,
            "now": _utc_now(),
        },
    )
    db.commit()
    return {"id": cid, **body.model_dump()}


@router.get("/operators")
def list_rental_operators(
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Query(None),
    network_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if tenant_id:
        clauses.append("o.tenant_id = :tenant_id")
        params["tenant_id"] = tenant_id
    if network_id:
        clauses.append("o.network_id = :network_id")
        params["network_id"] = network_id
    if status:
        clauses.append("o.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT o.id, o.tenant_id, o.network_id, n.code AS network_code, o.legal_name, o.trade_name,
                   o.operator_code, o.commission_bps, o.status, o.contract_ref, o.contact_email,
                   o.created_at, o.updated_at
            FROM rental_operators o
            LEFT JOIN rental_networks n ON n.id = o.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY o.legal_name
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/operators", status_code=status.HTTP_201_CREATED)
def create_rental_operator(body: RentalOperatorIn, db: Session = Depends(get_db)):
    dup = db.execute(
        text("SELECT id FROM rental_operators WHERE operator_code = :code"),
        {"code": body.operator_code.strip().upper()},
    ).mappings().first()
    if dup:
        raise HTTPException(status_code=409, detail={"type": "RENTAL_OPERATOR_EXISTS", "message": body.operator_code})
    oid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_operators (
                id, tenant_id, network_id, legal_name, trade_name, operator_code,
                commission_bps, status, contract_ref, contact_email, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :network_id, :legal_name, :trade_name, :operator_code,
                :commission_bps, :status, :contract_ref, :contact_email, :now, :now
            )
            """
        ),
        {
            "id": oid,
            "tenant_id": body.tenant_id,
            "network_id": body.network_id,
            "legal_name": body.legal_name,
            "trade_name": body.trade_name,
            "operator_code": body.operator_code.strip().upper(),
            "commission_bps": body.commission_bps,
            "status": body.status,
            "contract_ref": body.contract_ref,
            "contact_email": body.contact_email,
            "now": now,
        },
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT o.id, o.tenant_id, o.network_id, n.code AS network_code, o.legal_name, o.trade_name,
                   o.operator_code, o.commission_bps, o.status, o.contract_ref, o.contact_email,
                   o.created_at, o.updated_at
            FROM rental_operators o
            LEFT JOIN rental_networks n ON n.id = o.network_id
            WHERE o.id = :id
            """
        ),
        {"id": oid},
    ).mappings().first()
    return _serialize_row(row) if row else {"id": oid}


@router.patch("/operators/{operator_id}")
def update_rental_operator(operator_id: str, body: RentalOperatorUpdate, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_operators WHERE id = :id"), {"id": operator_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_OPERATOR_NOT_FOUND"})
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return {"ok": True}
    fields["id"] = operator_id
    fields["updated_at"] = _utc_now()
    sets = ", ".join(f"{k} = :{k}" for k in fields if k not in {"id", "updated_at"})
    db.execute(
        text(f"UPDATE rental_operators SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    db.commit()
    return {"ok": True, "id": operator_id}


@router.get("/contracts/{contract_id}/events")
def list_contract_events(
    contract_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": contract_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    rows = db.execute(
        text(
            """
            SELECT id, contract_id, event_type, payload_json, actor, created_at
            FROM rental_contract_events
            WHERE contract_id = :cid
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"cid": contract_id, "limit": limit},
    ).mappings().all()
    items = []
    for r in rows:
        item = _serialize_row(r)
        try:
            item["payload"] = json.loads(r.get("payload_json") or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        item.pop("payload_json", None)
        items.append(item)
    return {"items": items, "total": len(items)}


@router.get("/billing/invoices")
def list_billing_invoices(
    db: Session = Depends(get_db),
    contract_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if contract_id:
        clauses.append("contract_id = :contract_id")
        params["contract_id"] = contract_id
    if status:
        clauses.append("status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT id, contract_id, invoice_number, period_start, period_end, amount_cents,
                   currency, status, due_at, paid_at, created_at
            FROM rental_billing_invoices
            WHERE {" AND ".join(clauses)}
            ORDER BY period_end DESC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/billing/invoices", status_code=status.HTTP_201_CREATED)
def create_billing_invoice(body: RentalBillingInvoiceIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": body.contract_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_CONTRACT_NOT_FOUND"})
    inv_id = str(uuid.uuid4())
    inv_num = f"RNT-{body.contract_id[:8].upper()}-{int(_utc_now().timestamp()) % 1000000:06d}"
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO rental_billing_invoices (
                id, contract_id, invoice_number, period_start, period_end, amount_cents,
                currency, status, due_at, created_at, updated_at
            ) VALUES (
                :id, :contract_id, :invoice_number, :period_start, :period_end, :amount_cents,
                :currency, :status, :due_at, :now, :now
            )
            """
        ),
        {
            "id": inv_id,
            "contract_id": body.contract_id,
            "invoice_number": inv_num,
            "period_start": body.period_start,
            "period_end": body.period_end,
            "amount_cents": body.amount_cents,
            "currency": body.currency,
            "status": body.status,
            "due_at": body.due_at,
            "now": now,
        },
    )
    db.commit()
    return {"id": inv_id, "invoice_number": inv_num, **_serialize_row(body.model_dump())}


@router.patch("/billing/invoices/{invoice_id}")
def update_billing_invoice(invoice_id: str, body: RentalBillingInvoiceUpdate, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_billing_invoices WHERE id = :id"), {"id": invoice_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_INVOICE_NOT_FOUND"})
    fields = body.model_dump(exclude_unset=True)
    if body.status == "PAID" and "paid_at" not in fields:
        fields["paid_at"] = _utc_now()
    if not fields:
        return {"ok": True}
    fields["id"] = invoice_id
    fields["updated_at"] = _utc_now()
    sets = ", ".join(f"{k} = :{k}" for k in fields if k not in {"id", "updated_at"})
    db.execute(
        text(f"UPDATE rental_billing_invoices SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    db.commit()
    return {"ok": True, "id": invoice_id}


@router.get("/sla-policies")
def list_sla_policies(db: Session = Depends(get_db), network_id: Optional[str] = Query(None)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if network_id:
        clauses.append("s.network_id = :network_id")
        params["network_id"] = network_id
    rows = db.execute(
        text(
            f"""
            SELECT s.id, s.network_id, n.code AS network_code, s.metric_code, s.target_value,
                   s.unit, s.breach_penalty_bps, s.active, s.created_at
            FROM rental_sla_policies s
            JOIN rental_networks n ON n.id = s.network_id
            WHERE {" AND ".join(clauses)}
            ORDER BY n.name, s.metric_code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}


@router.post("/sla-policies", status_code=status.HTTP_201_CREATED)
def create_sla_policy(body: RentalSlaPolicyIn, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT id FROM rental_networks WHERE id = :id"), {"id": body.network_id}).mappings().first():
        raise HTTPException(status_code=404, detail={"type": "RENTAL_NETWORK_NOT_FOUND"})
    sid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO rental_sla_policies (
                id, network_id, metric_code, target_value, unit, breach_penalty_bps, active, created_at
            ) VALUES (
                :id, :network_id, :metric_code, :target_value, :unit, :breach_penalty_bps, :active, :now
            )
            """
        ),
        {
            "id": sid,
            "network_id": body.network_id,
            "metric_code": body.metric_code,
            "target_value": float(body.target_value),
            "unit": body.unit,
            "breach_penalty_bps": body.breach_penalty_bps,
            "active": body.active,
            "now": _utc_now(),
        },
    )
    db.commit()
    return {"id": sid, **body.model_dump(mode="json")}


@router.get("/webhook-deliveries")
def list_webhook_deliveries(
    db: Session = Depends(get_db),
    endpoint_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if endpoint_id:
        clauses.append("d.endpoint_id = :endpoint_id")
        params["endpoint_id"] = endpoint_id
    if status:
        clauses.append("d.status = :status")
        params["status"] = status
    rows = db.execute(
        text(
            f"""
            SELECT d.id, d.endpoint_id, e.tenant_id, d.contract_id, d.event_type, d.status,
                   d.attempt, d.response_code, d.error_message, d.next_retry_at, d.created_at
            FROM rental_webhook_deliveries d
            JOIN rental_webhook_endpoints e ON e.id = d.endpoint_id
            WHERE {" AND ".join(clauses)}
            ORDER BY d.created_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return {"items": [_serialize_row(r) for r in rows], "total": len(rows)}
