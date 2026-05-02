from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import bindparam, inspect, text
from sqlalchemy.orm import Session

from app.core.datetime_utils import to_iso_utc

logger = logging.getLogger(__name__)


def _serialize_value(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    return val


def fetch_ops_payment_reconciliation_snapshot(
    db: Session,
    *,
    reconciliation_status: str | None,
    reconciliation_batch_id: str | None,
    payment_status: str | None,
    split_status: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    bind = db.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())
    if "payment_transactions" not in tables:
        return {
            "total": 0,
            "transactions": [],
            "splits": [],
            "payment_splits_available": False,
        }

    pt_cols = {c["name"] for c in insp.get_columns("payment_transactions")}
    select_parts: list[str] = []
    for col in (
        "id",
        "order_id",
        "gateway",
        "status",
        "amount_cents",
        "initiated_at",
        "approved_at",
        "settled_at",
        "updated_at",
        "reconciliation_status",
        "reconciliation_batch_id",
    ):
        if col in pt_cols:
            select_parts.append(col)

    if not select_parts:
        return {
            "total": 0,
            "transactions": [],
            "splits": [],
            "payment_splits_available": "payment_splits" in tables,
        }

    where_sql: list[str] = ["1=1"]
    params: dict[str, Any] = {}

    rs = (reconciliation_status or "").strip().upper()
    if rs and "reconciliation_status" in pt_cols:
        where_sql.append("reconciliation_status = :reconciliation_status")
        params["reconciliation_status"] = rs

    rb = (reconciliation_batch_id or "").strip()
    if rb and "reconciliation_batch_id" in pt_cols:
        where_sql.append("reconciliation_batch_id = :reconciliation_batch_id")
        params["reconciliation_batch_id"] = rb

    ps = (payment_status or "").strip().upper()
    if ps and "status" in pt_cols:
        where_sql.append("status = :payment_status")
        params["payment_status"] = ps

    where_clause = " AND ".join(where_sql)
    count_sql = f"SELECT COUNT(*) AS c FROM payment_transactions WHERE {where_clause}"
    count_row = db.execute(text(count_sql), params).mappings().first()
    total = int(count_row["c"] if count_row and count_row.get("c") is not None else 0)

    nulls = " NULLS LAST" if bind.dialect.name == "postgresql" else ""
    order_col = "updated_at" if "updated_at" in select_parts else "id"
    list_sql = (
        f"SELECT {', '.join(select_parts)} FROM payment_transactions "
        f"WHERE {where_clause} ORDER BY {order_col} DESC{nulls}, id DESC "
        f"LIMIT :lim OFFSET :off"
    )
    list_params = {**params, "lim": limit, "off": offset}
    tx_rows = db.execute(text(list_sql), list_params).mappings().all()

    transactions: list[dict[str, Any]] = []
    order_ids: list[str] = []
    for row in tx_rows:
        d = dict(row)
        oid = str(d.get("order_id") or "")
        if oid and oid not in order_ids:
            order_ids.append(oid)
        out: dict[str, Any] = {
            "id": str(d.get("id") or ""),
            "order_id": oid,
            "gateway": str(d.get("gateway") or ""),
            "status": str(d.get("status") or ""),
            "amount_cents": int(d.get("amount_cents") or 0),
            "reconciliation_status": str(d["reconciliation_status"]).upper()
            if d.get("reconciliation_status") is not None
            else None,
            "reconciliation_batch_id": str(d["reconciliation_batch_id"])
            if d.get("reconciliation_batch_id") is not None
            else None,
            "initiated_at": to_iso_utc(d.get("initiated_at")),
            "approved_at": to_iso_utc(d.get("approved_at")),
            "settled_at": to_iso_utc(d.get("settled_at")),
            "updated_at": to_iso_utc(d.get("updated_at")),
        }
        transactions.append(out)

    splits_out: list[dict[str, Any]] = []
    payment_splits_available = "payment_splits" in tables
    if payment_splits_available and order_ids:
        ps_cols = {c["name"] for c in insp.get_columns("payment_splits")}
        split_select = [c for c in ("id", "order_id", "recipient_type", "recipient_id", "amount_cents", "percentage", "status", "settled_at", "created_at") if c in ps_cols]
        if split_select and "order_id" in split_select:
            where_splits = ["order_id IN :oids"]
            sparams: dict[str, Any] = {"oids": tuple(order_ids)}
            ss = (split_status or "").strip().upper()
            if ss and "status" in ps_cols:
                where_splits.append("status = :split_status")
                sparams["split_status"] = ss
            split_where = " AND ".join(where_splits)
            split_order = f"created_at DESC{nulls}, id DESC" if "created_at" in split_select else "id DESC"
            stmt = text(
                f"SELECT {', '.join(split_select)} FROM payment_splits WHERE {split_where} "
                f"ORDER BY {split_order}"
            ).bindparams(bindparam("oids", expanding=True))
            try:
                s_rows = db.execute(stmt, sparams).mappings().all()
            except Exception as exc:
                logger.warning("payment_splits_query_failed err=%s", exc)
                s_rows = []
            for s in s_rows:
                sd = dict(s)
                splits_out.append(
                    {
                        "id": str(sd.get("id") or ""),
                        "order_id": str(sd.get("order_id") or ""),
                        "recipient_type": str(sd.get("recipient_type") or ""),
                        "recipient_id": str(sd.get("recipient_id") or ""),
                        "amount_cents": int(sd.get("amount_cents") or 0),
                        "percentage": _serialize_value(sd.get("percentage")),
                        "status": str(sd.get("status") or ""),
                        "settled_at": to_iso_utc(sd.get("settled_at")),
                        "created_at": to_iso_utc(sd.get("created_at")),
                    }
                )

    return {
        "total": total,
        "transactions": transactions,
        "splits": splits_out,
        "payment_splits_available": payment_splits_available,
    }
