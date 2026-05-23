"""Cotação dinâmica de aluguel (rental_pricing_rules)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.rental_ops_common import utc_now as _utc_now


def resolve_rental_quote(
    db: Session,
    *,
    network_id: Optional[str] = None,
    slot_size: Optional[str] = "M",
    billing_cycle: str = "MONTHLY",
    at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Retorna cotação ou quoted=False se não houver regra."""
    at = at or _utc_now()
    size = (slot_size or "M").strip().upper()[:8]
    cycle = (billing_cycle or "MONTHLY").strip().upper()
    net_clause = "network_id IS NULL"
    params: dict[str, Any] = {"size": size, "cycle": cycle, "at": at}
    if network_id:
        net_clause = "(network_id = :nid OR network_id IS NULL)"
        params["nid"] = network_id
    try:
        row = db.execute(
            text(
                f"""
                SELECT id, code, name, base_amount_cents, surge_multiplier, network_id
                FROM rental_pricing_rules
                WHERE active = TRUE
                  AND {net_clause}
                  AND (slot_size IS NULL OR slot_size = :size)
                  AND (billing_cycle IS NULL OR billing_cycle = :cycle)
                  AND (valid_from IS NULL OR valid_from <= :at)
                  AND (valid_until IS NULL OR valid_until >= :at)
                ORDER BY
                  CASE WHEN network_id IS NOT NULL THEN 0 ELSE 1 END,
                  priority ASC
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()
    except Exception:
        return {"quoted": False, "amount_cents": None}

    if not row:
        return {"quoted": False, "amount_cents": None}

    amount = int(float(row["base_amount_cents"]) * float(row["surge_multiplier"]))
    return {
        "quoted": True,
        "amount_cents": amount,
        "currency": "BRL",
        "billing_cycle": cycle,
        "rule_code": str(row["code"]),
        "rule_name": str(row["name"]),
        "network_id": row.get("network_id"),
    }


def resolve_contract_pricing_context(
    db: Session,
    *,
    plan_id: Optional[str],
    locker_id: str,
    slot_label: str,
    network_id: Optional[str],
    slot_size: Optional[str],
    billing_cycle: Optional[str],
    amount_cents: Optional[int],
    use_dynamic_pricing: bool,
) -> dict[str, Any]:
    """Combina plano, slot e cotação dinâmica para preço final do contrato."""
    ctx: dict[str, Any] = {
        "amount_cents": amount_cents,
        "billing_cycle": billing_cycle,
        "currency": "BRL",
        "pricing_rule_code": None,
        "pricing_source": "manual",
    }
    if plan_id:
        prow = db.execute(
            text(
                """
                SELECT amount_cents, billing_cycle, currency
                FROM rental_plans WHERE id = :id LIMIT 1
                """
            ),
            {"id": plan_id},
        ).mappings().first()
        if not prow:
            return {"error": "RENTAL_PLAN_NOT_FOUND"}
        if ctx["amount_cents"] is None:
            ctx["amount_cents"] = int(prow["amount_cents"])
            ctx["pricing_source"] = "plan"
        ctx["billing_cycle"] = ctx["billing_cycle"] or str(prow["billing_cycle"])
        ctx["currency"] = str(prow.get("currency") or "BRL")
        try:
            extra = db.execute(
                text("SELECT network_id, slot_size FROM rental_plans WHERE id = :id LIMIT 1"),
                {"id": plan_id},
            ).mappings().first()
            if extra:
                network_id = network_id or (str(extra["network_id"]) if extra.get("network_id") else None)
                slot_size = slot_size or (str(extra["slot_size"]) if extra.get("slot_size") else None)
        except Exception:
            pass

    if not slot_size:
        srow = db.execute(
            text(
                """
                SELECT slot_size FROM locker_slots
                WHERE locker_id = :lid AND slot_label = :slot LIMIT 1
                """
            ),
            {"lid": locker_id, "slot": slot_label},
        ).mappings().first()
        if srow and srow.get("slot_size"):
            slot_size = str(srow["slot_size"])

    cycle = ctx["billing_cycle"] or "MONTHLY"
    if ctx["amount_cents"] is None and use_dynamic_pricing:
        quote = resolve_rental_quote(
            db,
            network_id=network_id,
            slot_size=slot_size or "M",
            billing_cycle=cycle,
        )
        if quote.get("quoted"):
            ctx["amount_cents"] = quote["amount_cents"]
            ctx["billing_cycle"] = quote.get("billing_cycle") or cycle
            ctx["currency"] = quote.get("currency") or "BRL"
            ctx["pricing_rule_code"] = quote.get("rule_code")
            ctx["pricing_source"] = "dynamic_quote"
            ctx["quote"] = quote
        else:
            return {"error": "NO_PRICING_RULE", "quote": quote}

    if ctx["amount_cents"] is None or not ctx["billing_cycle"]:
        return {"error": "RENTAL_CONTRACT_PRICING_REQUIRED"}

    return ctx
