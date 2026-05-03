"""
Modelo de elasticidade de preço (SKU/região) a partir de orders + order_items + allocations.

Elasticidade ≈ d ln Q / d ln P via regressão entre semanas (dados agregados).
"""
from __future__ import annotations

import math
from typing import Any

from app import db


def historical_elasticity_for_sku_region(sku_id: str, region: str) -> float:
    """
    Elasticidade log-log por SKU/região (180d).
    Valor negativo: demanda tende a cair quando o preço sobe.
    """
    rows = db.fetch_all(
        """
        WITH t AS (
          SELECT
            date_trunc('week', o.created_at)::date AS wk,
            AVG(LN(GREATEST(oi.unit_amount_cents::float, 1))) AS ln_p,
            SUM(oi.quantity)::float AS qty
          FROM order_items oi
          JOIN orders o ON o.id = oi.order_id
          JOIN allocations a ON a.order_id = o.id AND a.locker_id IS NOT NULL
          JOIN lockers lk ON lk.id = a.locker_id
          WHERE oi.sku_id = %s
            AND lk.region = %s
            AND o.created_at >= NOW() - INTERVAL '180 days'
            AND o.status IN ('PICKED_UP', 'DISPENSED', 'PAID_PENDING_PICKUP')
          GROUP BY 1
          HAVING SUM(oi.quantity) > 0
        )
        SELECT
          regr_slope(LN(GREATEST(qty, 0.5)), ln_p) AS beta,
          COUNT(*)::int AS n
        FROM t
        """,
        (sku_id, region),
    )
    if not rows or rows[0].get("n") is None or int(rows[0]["n"] or 0) < 4:
        return -1.0
    beta = rows[0].get("beta")
    if beta is None:
        return -1.0
    try:
        b = float(beta)
    except (TypeError, ValueError):
        return -1.0
    if not math.isfinite(b) or abs(b) > 8:
        return -1.0
    return float(b)


def demand_multiplier(elasticity: float, price_delta_pct: float) -> float:
    """
    Multiplicador de demanda aproximado: Q'/Q ≈ (1 + delta)^(elasticity)
    com delta = variação relativa de preço (ex.: 0.1 = +10%).
    """
    e = float(elasticity)
    d = float(price_delta_pct)
    # Limita expoente para estabilidade numérica
    expn = max(-3.0, min(3.0, e * math.log(max(0.65, 1.0 + d))))
    return float(math.exp(expn))


def revenue_proxy_cents(base_cents: int, price_delta_pct: float, elasticity: float) -> float:
    """Receita esperada ~ preço × demanda (proxy para ROI / bandit reward)."""
    p = max(1, int(base_cents)) * (1.0 + price_delta_pct)
    q = demand_multiplier(elasticity, price_delta_pct)
    return float(p * q)


def summarize_elasticity_panel(sku_id: str, region: str) -> dict[str, Any]:
    """Diagnóstico leve para dashboards (opcional)."""
    e = historical_elasticity_for_sku_region(sku_id, region)
    return {
        "sku_id": sku_id,
        "region": region,
        "elasticity_estimate": e,
        "interpretation": "inelástico" if abs(e) < 0.6 else ("elástico" if abs(e) > 1.2 else "moderado"),
    }
