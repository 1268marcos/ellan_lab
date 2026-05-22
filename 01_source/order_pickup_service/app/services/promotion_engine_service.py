"""Motor OPS: elegibilidade, match, simulação, conflitos e clone de promoções."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.promotion_discount import compute_promotion_discount
from app.services.promotion_scope_service import evaluate_promotion_scopes


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _json_load(raw, default=None):
    if default is None:
        default = {}
    if raw is None:
        return default
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default
    return default


def _table_exists(db: Session, name: str) -> bool:
    from sqlalchemy import inspect

    return name in set(inspect(db.get_bind()).get_table_names())


def record_promotion_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: str | None = None,
    correlation_id: str | None = None,
    payload: dict | None = None,
) -> None:
    if not _table_exists(db, "promotion_audit_events"):
        return
    meta_sql = (
        "CAST(:payload AS JSONB)"
        if db.get_bind().dialect.name == "postgresql"
        else ":payload"
    )
    db.execute(
        text(
            f"""
            INSERT INTO promotion_audit_events (
                id, entity_type, entity_id, action, actor_id, correlation_id, payload_json, created_at
            ) VALUES (
                :id, :et, :eid, :act, :actor, :corr, {meta_sql}, :at
            )
            """
        ),
        {
            "id": str(uuid4()),
            "et": entity_type,
            "eid": entity_id,
            "act": action,
            "actor": actor_id,
            "corr": correlation_id,
            "payload": json.dumps(payload or {}),
            "at": datetime.now(timezone.utc),
        },
    )


def evaluate_promotion_row(
    db: Session,
    promo: dict,
    *,
    order_id: str,
    total_amount_cents: int,
    items: list[dict] | None = None,
    country_code: str | None = None,
    channel_code: str | None = None,
    player_code: str | None = None,
    partner_id: str | None = None,
    marketplace_code: str | None = None,
) -> tuple[bool, str | None, int]:
    now = datetime.now(timezone.utc)
    code = str(promo.get("code") or "")
    if not bool(promo.get("is_active")):
        return False, "promoção inativa", 0
    valid_from = _parse_dt(promo.get("valid_from"))
    valid_until = _parse_dt(promo.get("valid_until"))
    if valid_from and valid_from > now:
        return False, "promoção ainda não vigente", 0
    if valid_until and valid_until < now:
        return False, "promoção expirada", 0
    if promo.get("max_uses") is not None and int(promo.get("uses_count") or 0) >= int(promo.get("max_uses") or 0):
        return False, "limite de uso atingido", 0
    total = int(total_amount_cents or 0)
    if total < int(promo.get("min_order_cents") or 0):
        return False, "pedido abaixo do mínimo", 0

    promo_id = str(promo.get("id") or "")
    scope_ok, scope_reason = evaluate_promotion_scopes(
        db,
        promo_id,
        country_code=country_code,
        channel_code=channel_code,
        player_code=player_code or marketplace_code,
        partner_id=partner_id,
        marketplace_code=marketplace_code,
    )
    if not scope_ok:
        return False, scope_reason or "fora do escopo", 0

    excl_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM promotion_product_exclusions WHERE promotion_id = :pid"),
            {"pid": promo_id},
        ).scalar()
        or 0
    )
    if excl_count > 0 and items:
        item_ids = {
            str(it.get("product_id") or it.get("sku_id") or "").strip()
            for it in items
            if isinstance(it, dict)
        }
        excluded = {
            str(r.get("product_id") or "")
            for r in db.execute(
                text("SELECT product_id FROM promotion_product_exclusions WHERE promotion_id = :pid"),
                {"pid": promo_id},
            ).mappings().all()
        }
        if item_ids & excluded:
            return False, "SKU excluído da promoção", 0

    incl_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM promotion_product_inclusions WHERE promotion_id = :pid"),
            {"pid": promo_id},
        ).scalar()
        or 0
    )
    if incl_count > 0:
        item_ids = {
            str(it.get("product_id") or it.get("sku_id") or "").strip()
            for it in (items or [])
            if isinstance(it, dict)
        }
        allowed = {
            str(r.get("product_id") or "")
            for r in db.execute(
                text("SELECT product_id FROM promotion_product_inclusions WHERE promotion_id = :pid"),
                {"pid": promo_id},
            ).mappings().all()
        }
        if not (item_ids & allowed):
            return False, "nenhum SKU na lista de inclusão", 0

    discount = compute_promotion_discount(
        promo_type=str(promo.get("type") or ""),
        total_amount_cents=total,
        discount_pct=(float(promo.get("discount_pct")) if promo.get("discount_pct") is not None else None),
        discount_cents=(int(promo.get("discount_cents")) if promo.get("discount_cents") is not None else None),
        max_discount_cents=(
            int(promo.get("max_discount_cents")) if promo.get("max_discount_cents") is not None else None
        ),
        conditions_json=_json_load(promo.get("conditions_json")),
        items=items or [],
    )
    return True, None, discount


def simulate_promotion(
    db: Session,
    *,
    promotion_code: str,
    order_id: str,
    total_amount_cents: int,
    items: list[dict] | None = None,
    country_code: str | None = None,
    channel_code: str | None = None,
    player_code: str | None = None,
    partner_id: str | None = None,
    marketplace_code: str | None = None,
) -> dict:
    code = str(promotion_code or "").strip()
    promo = db.execute(
        text(
            """
            SELECT id, code, name, type, discount_pct, discount_cents, min_order_cents, max_discount_cents,
                   max_uses, uses_count, is_active, valid_from, valid_until, conditions_json, campaign_id
            FROM promotions WHERE code = :code
            """
        ),
        {"code": code},
    ).mappings().first()
    if not promo:
        return {"valid": False, "reason": "promoção inexistente", "discount_cents": 0, "dry_run": True}
    valid, reason, discount = evaluate_promotion_row(
        db,
        dict(promo),
        order_id=order_id,
        total_amount_cents=total_amount_cents,
        items=items,
        country_code=country_code,
        channel_code=channel_code,
        player_code=player_code,
        partner_id=partner_id,
        marketplace_code=marketplace_code,
    )
    net = max(total_amount_cents - discount, 0) if valid else total_amount_cents
    return {
        "valid": valid,
        "reason": reason,
        "promotion_id": str(promo.get("id")),
        "promotion_code": code,
        "promotion_name": str(promo.get("name") or ""),
        "promotion_type": str(promo.get("type") or ""),
        "discount_cents": discount,
        "total_amount_cents": total_amount_cents,
        "net_amount_cents": net,
        "dry_run": True,
        "would_redeem": valid,
    }


def match_promotions(
    db: Session,
    *,
    total_amount_cents: int,
    items: list[dict] | None = None,
    country_code: str | None = None,
    channel_code: str | None = None,
    player_code: str | None = None,
    partner_id: str | None = None,
    marketplace_code: str | None = None,
    limit: int = 10,
) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT id, code, name, type, discount_pct, discount_cents, min_order_cents, max_discount_cents,
                   max_uses, uses_count, is_active, valid_from, valid_until, conditions_json
            FROM promotions WHERE is_active = TRUE ORDER BY code
            """
        ),
    ).mappings().all()
    matches: list[dict] = []
    for row in rows:
        valid, reason, discount = evaluate_promotion_row(
            db,
            dict(row),
            order_id="MATCH-PREVIEW",
            total_amount_cents=total_amount_cents,
            items=items,
            country_code=country_code,
            channel_code=channel_code,
            player_code=player_code,
            partner_id=partner_id,
            marketplace_code=marketplace_code,
        )
        matches.append(
            {
                "promotion_id": str(row.get("id")),
                "promotion_code": str(row.get("code") or ""),
                "promotion_name": str(row.get("name") or ""),
                "eligible": valid,
                "reason": reason,
                "estimated_discount_cents": discount if valid else 0,
            }
        )
    matches.sort(key=lambda m: (0 if m["eligible"] else 1, -m["estimated_discount_cents"]))
    return matches[: max(1, min(limit, 50))]


def detect_scope_conflicts(db: Session, *, limit: int = 50) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT p.id, p.code, p.name, s.scope_type, s.scope_value, s.mode
            FROM promotions p
            JOIN promotion_scopes s ON s.promotion_id = p.id
            WHERE p.is_active = TRUE AND s.mode = 'INCLUDE'
            ORDER BY s.scope_type, s.scope_value, p.code
            """
        ),
    ).mappings().all()
    buckets: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = (str(r.get("scope_type") or ""), str(r.get("scope_value") or ""))
        buckets.setdefault(key, []).append(dict(r))
    conflicts: list[dict] = []
    for (st, sv), promos in buckets.items():
        if len(promos) < 2:
            continue
        conflicts.append(
            {
                "scope_type": st,
                "scope_value": sv,
                "promotions_count": len(promos),
                "promotions": [
                    {"id": p.get("id"), "code": p.get("code"), "name": p.get("name")} for p in promos
                ],
                "hint": "Múltiplas promoções ativas no mesmo escopo — rever stacking da campanha.",
            }
        )
    conflicts.sort(key=lambda c: -c["promotions_count"])
    return conflicts[: max(1, min(limit, 200))]


def player_promotion_matrix(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT s.scope_value AS player_code, COUNT(DISTINCT p.id) AS active_promotions
            FROM promotion_scopes s
            JOIN promotions p ON p.id = s.promotion_id
            WHERE p.is_active = TRUE
              AND s.mode = 'INCLUDE'
              AND s.scope_type IN ('PLAYER', 'LOCKER_OPERATOR', 'MARKETPLACE')
            GROUP BY s.scope_value
            ORDER BY active_promotions DESC, player_code
            LIMIT 30
            """
        ),
    ).mappings().all()
    return [
        {"player_code": str(r.get("player_code") or ""), "active_promotions": int(r.get("active_promotions") or 0)}
        for r in rows
    ]


def resolve_promotion_id(db: Session, promotion_id_or_code: str) -> str:
    """Resolve UUID ou código (ex.: marcos10) para id da promoção."""
    raw = str(promotion_id_or_code or "").strip()
    if not raw:
        raise ValueError("PROMOTION_NOT_FOUND")
    by_id = db.execute(text("SELECT id FROM promotions WHERE id = :id"), {"id": raw}).mappings().first()
    if by_id:
        return str(by_id.get("id") or raw)
    by_code = db.execute(
        text("SELECT id FROM promotions WHERE UPPER(code) = :code"),
        {"code": raw.upper()},
    ).mappings().first()
    if by_code:
        return str(by_code.get("id") or "")
    raise ValueError("PROMOTION_NOT_FOUND")


def clone_promotion(
    db: Session,
    *,
    source_promotion_id: str,
    new_code: str,
    new_name: str | None = None,
    actor_id: str | None = None,
) -> dict:
    resolved_id = resolve_promotion_id(db, source_promotion_id)
    src = db.execute(text("SELECT * FROM promotions WHERE id = :id"), {"id": resolved_id}).mappings().first()
    if not src:
        raise ValueError("PROMOTION_NOT_FOUND")
    code = str(new_code).strip().upper()
    if db.execute(text("SELECT 1 FROM promotions WHERE code = :c"), {"c": code}).scalar():
        raise ValueError("CODE_ALREADY_EXISTS")
    new_id = str(uuid4())
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            f"""
            INSERT INTO promotions (
                id, code, name, type, discount_pct, discount_cents, min_order_cents,
                max_discount_cents, max_uses, uses_count, per_user_limit, conditions_json,
                is_active, valid_from, valid_until, created_by, created_at, updated_at
            )
            SELECT
                :new_id, :new_code, :new_name, type, discount_pct, discount_cents, min_order_cents,
                max_discount_cents, max_uses, 0, per_user_limit, conditions_json,
                FALSE, valid_from, valid_until, :actor, :at, :at
            FROM promotions WHERE id = :src_id
            """
        ),
        {
            "new_id": new_id,
            "new_code": code,
            "new_name": new_name or f"{src.get('name')} (cópia)",
            "actor": actor_id,
            "src_id": resolved_id,
            "at": now,
        },
    )
    for table, cols in (
        ("promotion_scopes", "id, promotion_id, scope_type, scope_value, mode, notes, created_at"),
        ("promotion_product_exclusions", "promotion_id, product_id"),
        ("promotion_product_inclusions", "promotion_id, product_id"),
    ):
        if not _table_exists(db, table):
            continue
        if table == "promotion_scopes":
            scopes = db.execute(
                text("SELECT scope_type, scope_value, mode, notes FROM promotion_scopes WHERE promotion_id = :pid"),
                {"pid": resolved_id},
            ).mappings().all()
            for sc in scopes:
                db.execute(
                    text(
                        """
                        INSERT INTO promotion_scopes (id, promotion_id, scope_type, scope_value, mode, notes, created_at)
                        VALUES (:id, :pid, :st, :sv, :m, :n, :at)
                        """
                    ),
                    {
                        "id": str(uuid4()),
                        "pid": new_id,
                        "st": sc.get("scope_type"),
                        "sv": sc.get("scope_value"),
                        "m": sc.get("mode"),
                        "n": sc.get("notes"),
                        "at": now,
                    },
                )
        elif table == "promotion_product_exclusions":
            for ex in db.execute(
                text("SELECT product_id FROM promotion_product_exclusions WHERE promotion_id = :pid"),
                {"pid": resolved_id},
            ).mappings().all():
                db.execute(
                    text(
                        "INSERT INTO promotion_product_exclusions (promotion_id, product_id) VALUES (:pid, :pr)"
                    ),
                    {"pid": new_id, "pr": ex.get("product_id")},
                )
        elif table == "promotion_product_inclusions":
            for inc in db.execute(
                text("SELECT product_id FROM promotion_product_inclusions WHERE promotion_id = :pid"),
                {"pid": resolved_id},
            ).mappings().all():
                db.execute(
                    text(
                        "INSERT INTO promotion_product_inclusions (promotion_id, product_id) VALUES (:pid, :pr)"
                    ),
                    {"pid": new_id, "pr": inc.get("product_id")},
                )
    record_promotion_audit(
        db,
        entity_type="promotion",
        entity_id=new_id,
        action="CLONED",
        actor_id=actor_id,
        payload={"source_id": resolved_id, "new_code": code},
    )
    db.commit()
    return {"promotion_id": new_id, "promotion_code": code, "source_id": resolved_id}
