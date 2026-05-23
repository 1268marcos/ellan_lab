"""Seguro de conteúdo em slot alugado."""
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.rental_ops_common import utc_now as _utc_now

# 2% do valor declarado, mínimo R$ 5,00, teto R$ 500/mês de prêmio
_DEFAULT_RATE_BPS = 200
_MIN_PREMIUM_CENTS = 500
_MAX_PREMIUM_CENTS = 50000
_COVERAGE_MULTIPLIER = 1.0


def calculate_content_insurance_premium(declared_value_cents: int) -> dict[str, int]:
    declared = max(0, int(declared_value_cents))
    premium = int(declared * _DEFAULT_RATE_BPS / 10000)
    premium = max(_MIN_PREMIUM_CENTS, min(premium, _MAX_PREMIUM_CENTS))
    coverage = int(declared * _COVERAGE_MULTIPLIER)
    return {"premium_cents": premium, "coverage_cents": coverage, "declared_value_cents": declared}


def create_content_insurance(
    db: Session,
    *,
    contract_id: str,
    declared_value_cents: int,
    currency: str = "BRL",
    months: int = 1,
) -> dict[str, Any] | None:
    """Cria apólice ACTIVE vinculada ao contrato."""
    try:
        if db.execute(
            text("SELECT id FROM rental_content_insurance WHERE contract_id = :c AND status = 'ACTIVE' LIMIT 1"),
            {"c": contract_id},
        ).mappings().first():
            return None
    except Exception:
        return None

    calc = calculate_content_insurance_premium(declared_value_cents)
    now = _utc_now()
    iid = str(uuid.uuid4())
    policy_number = f"RCI-{contract_id[:8].upper()}-{uuid.uuid4().hex[:6].upper()}"
    db.execute(
        text(
            """
            INSERT INTO rental_content_insurance (
                id, contract_id, policy_number, declared_value_cents, premium_cents,
                coverage_cents, currency, status, starts_at, ends_at, created_at, updated_at
            ) VALUES (
                :id, :cid, :pn, :decl, :prem, :cov, :cur, 'ACTIVE', :start, :end, :now, :now
            )
            """
        ),
        {
            "id": iid,
            "cid": contract_id,
            "pn": policy_number,
            "decl": calc["declared_value_cents"],
            "prem": calc["premium_cents"],
            "cov": calc["coverage_cents"],
            "cur": currency,
            "start": now,
            "end": now + timedelta(days=30 * max(1, months)),
            "now": now,
        },
    )
    return {"id": iid, "policy_number": policy_number, **calc}
