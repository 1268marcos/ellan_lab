"""Validação e resgate de cupons de assinatura."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_utc(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_plans_json(raw: Any) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return [str(p).upper() for p in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def validate_promo(
    db: Session,
    *,
    code: str,
    user_id: str,
    plan_code: str,
) -> dict[str, Any]:
    promo_code = code.strip().upper()
    plan = plan_code.strip().upper()
    now = _utc_now()
    row = db.execute(
        text("SELECT * FROM subscription_promo_codes WHERE code = :c AND active = TRUE LIMIT 1"),
        {"c": promo_code},
    ).mappings().first()
    if not row:
        return {"ok": True, "valid": False, "reason": "PROMO_NOT_FOUND"}

    valid_from = _coerce_utc(row.get("valid_from"))
    valid_until = _coerce_utc(row.get("valid_until"))
    if valid_from and valid_from > now:
        return {"ok": True, "valid": False, "reason": "PROMO_NOT_STARTED"}
    if valid_until and valid_until < now:
        return {"ok": True, "valid": False, "reason": "PROMO_EXPIRED"}

    max_r = row.get("max_redemptions")
    if max_r is not None and int(row.get("redemption_count") or 0) >= int(max_r):
        return {"ok": True, "valid": False, "reason": "PROMO_EXHAUSTED"}

    plans = _parse_plans_json(row.get("eligible_plans_json"))
    if plans and plan not in plans:
        return {"ok": True, "valid": False, "reason": "PLAN_NOT_ELIGIBLE"}

    already = db.execute(
        text(
            """
            SELECT 1 FROM subscription_promo_redemptions pr
            JOIN subscription_promo_codes pc ON pc.id = pr.promo_code_id
            WHERE pc.code = :c AND pr.user_id = :u LIMIT 1
            """
        ),
        {"c": promo_code, "u": user_id.strip()},
    ).scalar()
    if already:
        return {"ok": True, "valid": False, "reason": "ALREADY_REDEEMED"}

    plan_row = db.execute(
        text("SELECT monthly_fee_cents FROM subscription_plans WHERE code = :p AND is_active = TRUE LIMIT 1"),
        {"p": plan},
    ).mappings().first()
    base = int(plan_row["monthly_fee_cents"]) if plan_row else 0
    pct = float(row.get("discount_pct") or 0)
    disc_cents = int(row.get("discount_cents") or 0)
    discount = disc_cents + int(base * pct / 100) if base else disc_cents

    return {
        "ok": True,
        "valid": True,
        "code": promo_code,
        "promo_code_id": str(row["id"]),
        "discount_cents": discount,
        "discount_pct": pct,
        "bonus_months": int(row.get("bonus_months") or 0),
        "description": row.get("description"),
    }


def redeem_promo(
    db: Session,
    *,
    code: str,
    user_id: str,
    plan_code: str,
    subscription_id: str,
) -> dict[str, Any]:
    """Valida e grava resgate; incrementa redemption_count. Não faz commit."""
    result = validate_promo(db, code=code, user_id=user_id, plan_code=plan_code)
    if not result.get("valid"):
        raise ValueError(f"PROMO_INVALID:{result.get('reason', 'UNKNOWN')}")

    now = _utc_now()
    rid = str(uuid.uuid4())
    discount = int(result["discount_cents"])
    db.execute(
        text(
            """
            INSERT INTO subscription_promo_redemptions (
                id, promo_code_id, user_id, subscription_id, discount_applied_cents, redeemed_at
            ) VALUES (:id, :pid, :uid, :sid, :disc, :now)
            """
        ),
        {
            "id": rid,
            "pid": result["promo_code_id"],
            "uid": user_id.strip(),
            "sid": subscription_id,
            "disc": discount,
            "now": now,
        },
    )
    db.execute(
        text(
            """
            UPDATE subscription_promo_codes
            SET redemption_count = redemption_count + 1, updated_at = :now
            WHERE id = :pid
            """
        ),
        {"pid": result["promo_code_id"], "now": now},
    )
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, 'subscription.promo_redeemed', :uid, :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": subscription_id,
            "uid": user_id.strip(),
            "payload": json.dumps(
                {
                    "promo_code": result["code"],
                    "discount_cents": discount,
                    "bonus_months": result["bonus_months"],
                }
            ),
            "now": now,
        },
    )
    return {
        "promo_code": result["code"],
        "discount_cents": discount,
        "discount_pct": float(result["discount_pct"]),
        "bonus_months": int(result["bonus_months"]),
        "redemption_id": rid,
    }
