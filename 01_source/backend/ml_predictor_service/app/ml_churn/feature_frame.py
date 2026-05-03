"""Agrega features rolling ~90d por logistics_partners.id."""
from __future__ import annotations

import pandas as pd

from app import db

FEATURE_COLS = [
    "avg_pickup_delay_hours",
    "sla_compliance_rate_pct",
    "penalty_amount_cents",
    "dispute_frequency",
    "volume_deliveries_trend",
    "payment_delay_days",
    "credit_notes_total",
]


def load_training_frame() -> pd.DataFrame:
    partners = db.fetch_all(
        """
        SELECT lp.id AS partner_id, lp.name, lp.code, lp.active,
          CASE
            WHEN lp.active IS FALSE THEN 1
            WHEN EXISTS (
              SELECT 1 FROM partner_billing_cycles x
              WHERE x.partner_id = lp.id AND x.status = 'CANCELLED'
                AND COALESCE(x.updated_at, x.created_at) >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '30 days')
            ) THEN 1
            WHEN EXISTS (
              SELECT 1 FROM partner_sla_agreements s
              WHERE s.partner_id = lp.id AND COALESCE(s.is_active, true)
                AND s.valid_until IS NOT NULL
                AND s.valid_until < (CURRENT_DATE + INTERVAL '30 days')
            ) THEN 1
            ELSE 0
          END::int AS churn_next_30d
        FROM logistics_partners lp
        """
    )
    df = pd.DataFrame(partners)
    if df.empty:
        return df
    ppm = db.fetch_all(
        """
        SELECT partner_id,
          AVG(COALESCE(avg_pickup_hours, 0))::float AS avg_pickup_delay_hours,
          AVG(COALESCE(sla_compliance_pct, 0))::float AS sla_compliance_rate_pct
        FROM partner_performance_metrics
        WHERE period_month >= to_char((CURRENT_DATE - INTERVAL '90 days'), 'YYYY-MM')
        GROUP BY partner_id
        """
    )
    pen = db.fetch_all(
        """
        SELECT partner_id, SUM(COALESCE(sla_penalty_cents, 0))::float AS penalty_amount_cents
        FROM partner_billing_cycles
        WHERE period_end >= (CURRENT_DATE - INTERVAL '90 days')
        GROUP BY partner_id
        """
    )
    disp = db.fetch_all(
        """
        SELECT partner_id,
          (COUNT(*) FILTER (WHERE status = 'DISPUTED' OR dispute_reason IS NOT NULL)::float / 3.0) AS dispute_frequency
        FROM partner_billing_cycles
        WHERE period_end >= (CURRENT_DATE - INTERVAL '90 days')
        GROUP BY partner_id
        """
    )
    vol = db.fetch_all(
        """
        WITH g AS (
          SELECT partner_id,
            SUM(CASE WHEN period_end >= (CURRENT_DATE - INTERVAL '30 days') THEN COALESCE(total_deliveries, 0) ELSE 0 END) AS d30,
            SUM(CASE WHEN period_end < (CURRENT_DATE - INTERVAL '30 days')
                      AND period_end >= (CURRENT_DATE - INTERVAL '90 days') THEN COALESCE(total_deliveries, 0) ELSE 0 END) AS d60
          FROM partner_billing_cycles
          WHERE period_end >= (CURRENT_DATE - INTERVAL '90 days')
          GROUP BY partner_id
        )
        SELECT partner_id,
          CASE WHEN d60 > 0 THEN (d30::float / NULLIF(d60 / 2.0, 0)) - 1.0 ELSE 0.0 END AS volume_deliveries_trend
        FROM g
        """
    )
    pay = db.fetch_all(
        """
        SELECT partner_id,
          AVG(EXTRACT(EPOCH FROM (paid_at - invoiced_at)) / 86400.0)::float AS payment_delay_days
        FROM partner_billing_cycles
        WHERE period_end >= (CURRENT_DATE - INTERVAL '90 days')
          AND paid_at IS NOT NULL AND invoiced_at IS NOT NULL
        GROUP BY partner_id
        """
    )
    cr = db.fetch_all(
        """
        SELECT partner_id, SUM(COALESCE(amount_cents, 0))::float AS credit_notes_total
        FROM partner_credit_notes
        WHERE created_at >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '90 days')
          AND status IN ('APPROVED', 'APPLIED', 'PENDING')
        GROUP BY partner_id
        """
    )
    for name, rows in (
        ("ppm", ppm),
        ("pen", pen),
        ("disp", disp),
        ("vol", vol),
        ("pay", pay),
        ("cr", cr),
    ):
        d = pd.DataFrame(rows)
        if d.empty:
            continue
        df = df.merge(d, on="partner_id", how="left")
    for c in FEATURE_COLS:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = df[c].fillna(0.0).astype(float)
    return df
