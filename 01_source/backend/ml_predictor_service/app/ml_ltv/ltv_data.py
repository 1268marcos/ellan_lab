"""Queries e carregamento de dados para LTV (pedidos, pagamentos, consentes, notificações)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app import db

# Pedidos pagos com valor monetário por transação (uma linha por order).
TRANSACTIONS_SQL = """
WITH paid_orders AS (
    SELECT
        o.id AS order_id,
        o.user_id::text AS user_id,
        COALESCE(o.paid_at, o.created_at)::timestamp AS purchase_at,
        COALESCE(
            (
                SELECT SUM(pt.amount_cents)::bigint
                FROM payment_transactions pt
                WHERE pt.order_id = o.id
                  AND UPPER(COALESCE(pt.status, '')) IN ('APPROVED', 'AUTHORIZED', 'SETTLED', 'CAPTURED')
            ),
            o.amount_cents::bigint
        ) AS amount_cents
    FROM orders o
    WHERE o.user_id IS NOT NULL
      AND o.deleted_at IS NULL
      AND (
          o.paid_at IS NOT NULL
          OR o.status::text IN (
              'PAID_PENDING_PICKUP', 'DISPENSED', 'PICKED_UP'
          )
      )
)
SELECT user_id AS customer_id,
       purchase_at AS datetime,
       GREATEST(amount_cents, 0)::float / 100.0 AS monetary_value
FROM paid_orders
WHERE amount_cents IS NOT NULL AND amount_cents > 0
ORDER BY user_id, purchase_at
"""

# Features comportamentais 90d + região/país + consentes + engajamento notificações.
FEATURES_90D_SQL = """
WITH win AS (
    SELECT NOW() AT TIME ZONE 'UTC' AS t1,
           (NOW() AT TIME ZONE 'UTC' - INTERVAL '90 days') AS t0
),
ord_90 AS (
    SELECT o.*
    FROM orders o, win w
    WHERE o.user_id IS NOT NULL
      AND o.deleted_at IS NULL
      AND o.created_at >= w.t0
      AND o.created_at < w.t1
),
pay AS (
    SELECT pt.order_id, SUM(pt.amount_cents)::bigint AS cents
    FROM payment_transactions pt, win w
    WHERE pt.created_at >= w.t0
      AND UPPER(COALESCE(pt.status, '')) IN ('APPROVED', 'AUTHORIZED', 'SETTLED', 'CAPTURED')
    GROUP BY pt.order_id
),
ord_pay AS (
    SELECT o.user_id::text AS user_id,
           o.id AS order_id,
           o.created_at,
           o.channel::text AS channel,
           o.region,
           COALESCE(pay.cents, o.amount_cents::bigint, 0) AS line_cents,
           EXTRACT(HOUR FROM (o.created_at AT TIME ZONE 'UTC'))::int AS hour_utc,
           COALESCE(pr.category_id, 'UNKNOWN') AS category_id
    FROM ord_90 o
    LEFT JOIN pay ON pay.order_id = o.id
    LEFT JOIN products pr ON pr.id = o.sku_id
),
agg AS (
    SELECT op.user_id,
           SUM(op.line_cents)::bigint AS total_gasto_cents,
           COUNT(*)::int AS frequencia_compras,
           MAX(op.created_at) AS last_purchase_at,
           AVG(op.line_cents)::float AS ticket_medio_cents,
           COUNT(DISTINCT op.channel)::int AS n_channels,
           BOOL_OR(op.channel = 'ONLINE') AS used_online,
           BOOL_OR(op.channel = 'KIOSK') AS used_kiosk,
           MODE() WITHIN GROUP (ORDER BY op.category_id) AS produtos_categoria_preferida,
           MODE() WITHIN GROUP (ORDER BY op.hour_utc) AS horario_preferido_compras,
           MODE() WITHIN GROUP (ORDER BY op.region) AS region_mode
    FROM ord_pay op
    GROUP BY op.user_id
),
notif AS (
    SELECT nl.user_id::text AS user_id,
           COUNT(*)::int AS notification_engagement_90d
    FROM notification_logs nl, win w
    WHERE nl.user_id IS NOT NULL
      AND nl.created_at >= w.t0
      AND nl.created_at < w.t1
      AND (nl.delivered_at IS NOT NULL OR LOWER(COALESCE(nl.status, '')) IN ('delivered', 'sent', 'opened'))
    GROUP BY nl.user_id
),
consent AS (
    SELECT pc.user_id::text AS user_id,
           BOOL_OR(pc.consent_type = 'ANALYTICS' AND pc.granted = true AND pc.revoked_at IS NULL) AS consent_analytics,
           BOOL_OR(pc.consent_type = 'MARKETING' AND pc.granted = true AND pc.revoked_at IS NULL) AS consent_marketing
    FROM privacy_consents pc
    WHERE pc.user_id IS NOT NULL
    GROUP BY pc.user_id
)
SELECT u.id::text AS user_id,
       u.tax_country AS country_code,
       COALESCE(a.total_gasto_cents, 0)::bigint AS total_gasto_cents,
       COALESCE(a.frequencia_compras, 0)::int AS frequencia_compras,
       CASE WHEN a.last_purchase_at IS NULL THEN NULL
            ELSE EXTRACT(EPOCH FROM (w.t1 - a.last_purchase_at)) / 86400.0
       END AS recencia_ultima_compra_dias,
       COALESCE(a.ticket_medio_cents, 0)::float AS ticket_medio_cents,
       COALESCE(a.used_online, false) AS used_online,
       COALESCE(a.used_kiosk, false) AS used_kiosk,
       COALESCE(a.n_channels, 0)::int AS n_channels_distinct,
       COALESCE(a.produtos_categoria_preferida, 'UNKNOWN') AS produtos_categoria_preferida,
       COALESCE(a.horario_preferido_compras, 12)::int AS horario_preferido_compras,
       COALESCE(a.region_mode, '') AS region,
       COALESCE(n.notification_engagement_90d, 0)::int AS notification_engagement_90d,
       COALESCE(c.consent_analytics, false) AS consent_analytics,
       COALESCE(c.consent_marketing, false) AS consent_marketing
FROM users u
CROSS JOIN win w
LEFT JOIN agg a ON a.user_id = u.id::text
LEFT JOIN notif n ON n.user_id = u.id::text
LEFT JOIN consent c ON c.user_id = u.id::text
WHERE u.deleted_at IS NULL AND u.anonymized_at IS NULL
"""


def load_transactions_df() -> pd.DataFrame:
    rows = db.fetch_all(TRANSACTIONS_SQL)
    if not rows:
        return pd.DataFrame(columns=["customer_id", "datetime", "monetary_value"])
    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df


def load_features_90d_df() -> pd.DataFrame:
    rows = db.fetch_all(FEATURES_90D_SQL)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def user_consent_flags(user_id: str) -> dict[str, bool]:
    row = db.fetch_one(
        """
        SELECT
            BOOL_OR(consent_type = 'ANALYTICS' AND granted = true AND revoked_at IS NULL) AS consent_analytics,
            BOOL_OR(consent_type = 'MARKETING' AND granted = true AND revoked_at IS NULL) AS consent_marketing
        FROM privacy_consents
        WHERE user_id::text = %s
        """,
        (user_id,),
    )
    if not row:
        return {"consent_analytics": False, "consent_marketing": False}
    return {
        "consent_analytics": bool(row.get("consent_analytics")),
        "consent_marketing": bool(row.get("consent_marketing")),
    }


def user_exists(user_id: str) -> bool:
    r = db.fetch_one(
        "SELECT 1 AS ok FROM users WHERE id::text = %s AND deleted_at IS NULL AND anonymized_at IS NULL",
        (user_id,),
    )
    return bool(r)


def observation_period_end() -> datetime:
    return datetime.now(timezone.utc)
