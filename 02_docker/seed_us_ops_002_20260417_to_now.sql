BEGIN;

-- Seed idempotente para validação operacional final do US-OPS-002
-- Janela: 2026-04-17 00:00:00+00 até now()
-- Lockers:
--   - SP-ALPHAVILLE-SHOP-LK-001
--   - SP-CARAPICUIBA-JDMARILU-LK-001
--   - PT-MAIA-CENTRO-LK-001
--
-- Observação:
-- details_json nesta base está em TEXT. Mantemos payload JSON serializado
-- para permitir rastreio por seed_tag.

DELETE FROM public.ops_action_audit
WHERE details_json LIKE '%"seed_tag":"US-OPS-002-OPERACIONAL-2026-04-17"%';

WITH lockers(locker_id) AS (
  VALUES
    ('SP-ALPHAVILLE-SHOP-LK-001'),
    ('SP-CARAPICUIBA-JDMARILU-LK-001'),
    ('PT-MAIA-CENTRO-LK-001')
),
hours AS (
  SELECT generate_series(
    TIMESTAMPTZ '2026-04-17 00:00:00+00',
    now(),
    INTERVAL '1 hour'
  ) AS bucket_ts
),
base AS (
  SELECT
    h.bucket_ts,
    l.locker_id,
    CASE
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-22 00:00:00+00' THEN 2
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-26 00:00:00+00' THEN 3
      ELSE 4
    END AS actions_per_hour,
    CASE
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-22 00:00:00+00' THEN 8
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-26 00:00:00+00' THEN 24
      ELSE 56
    END AS error_threshold_pct,
    CASE
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-22 00:00:00+00' THEN 85
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-26 00:00:00+00' THEN 130
      ELSE 210
    END AS base_latency_ms,
    CASE
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-22 00:00:00+00' THEN 35
      WHEN h.bucket_ts < TIMESTAMPTZ '2026-04-26 00:00:00+00' THEN 55
      ELSE 90
    END AS jitter_ms
  FROM hours h
  CROSS JOIN lockers l
),
expanded AS (
  SELECT
    b.*,
    i.slot_idx,
    (
      b.bucket_ts
      + ((i.slot_idx - 1) * (60.0 / b.actions_per_hour)) * INTERVAL '1 minute'
    ) AS created_at
  FROM base b
  CROSS JOIN LATERAL generate_series(1, b.actions_per_hour) AS i(slot_idx)
),
scored AS (
  SELECT
    e.*,
    abs(('x' || substr(md5(e.locker_id || '|' || e.created_at::text || '|' || e.slot_idx::text), 1, 8))::bit(32)::int) % 100 AS score_pct,
    abs(('x' || substr(md5('lat|' || e.locker_id || '|' || e.created_at::text || '|' || e.slot_idx::text), 1, 8))::bit(32)::int) % 100 AS latency_rand
  FROM expanded e
)
INSERT INTO public.ops_action_audit (
  id,
  action,
  result,
  correlation_id,
  user_id,
  role,
  order_id,
  error_message,
  details_json,
  created_at
)
SELECT
  ('oaa_seed_' || substr(md5(gen_random_uuid()::text), 1, 24))::varchar(40) AS id,
  CASE
    WHEN (score_pct % 100) < 45 THEN 'OPS_RECON_PENDING_RUN_ONCE'
    ELSE 'OPS_METRICS_VIEW'
  END::varchar(120) AS action,
  CASE
    WHEN score_pct < error_threshold_pct THEN 'ERROR'
    ELSE 'SUCCESS'
  END::varchar(20) AS result,
  ('corr-seed-' || substr(md5(gen_random_uuid()::text), 1, 20))::varchar(80) AS correlation_id,
  'seed-ops'::varchar(36) AS user_id,
  'admin_operacao'::varchar(80) AS role,
  ('seed-' || substr(md5(gen_random_uuid()::text), 1, 30))::varchar(36) AS order_id,
  CASE
    WHEN score_pct >= error_threshold_pct THEN NULL
    WHEN (score_pct % 5) = 0 THEN ('timeout while contacting locker gateway (' || locker_id || ')')
    WHEN (score_pct % 5) = 1 THEN ('locker integration http 504 for ' || locker_id)
    WHEN (score_pct % 5) = 2 THEN ('validacao de payload operacional para ' || locker_id)
    WHEN (score_pct % 5) = 3 THEN ('upstream integration error for locker ' || locker_id)
    ELSE ('infra queue delay processing locker ' || locker_id)
  END AS error_message,
  (
    '{"seed_tag":"US-OPS-002-OPERACIONAL-2026-04-17",'
    || '"locker_id":"' || locker_id || '",'
    || '"duration_ms":' || to_char(greatest(20.0, base_latency_ms + ((latency_rand / 100.0) * (2 * jitter_ms) - jitter_ms)), 'FM999990.00') || ','
    || '"metrics":{"latency_ms":' || to_char(greatest(20.0, base_latency_ms + ((latency_rand / 100.0) * (2 * jitter_ms) - jitter_ms)), 'FM999990.00') || '},'
    || '"source":"seed_us_ops_002_20260417_to_now.sql"}'
  )::text AS details_json,
  created_at
FROM scored
ORDER BY created_at, locker_id, slot_idx;

COMMIT;
