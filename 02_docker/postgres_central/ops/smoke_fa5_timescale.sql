-- smoke_fa5_timescale.sql
-- Smoke único para validar bloco Timescale do FA-5 em qualquer ambiente.
--
-- Uso:
--   psql -U <user> -d <db> -f smoke_fa5_timescale.sql
--
-- Resultado esperado:
-- 1) ext_ok = true
-- 2) hypertable_count = 3
-- 3) policy_count = 6
-- 4) dedupe_index_count = 2
-- 5) Resultado final: SMOKE_OK

\echo '== FA-5 Timescale smoke: start =='

WITH ext AS (
    SELECT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) AS ext_ok
),
hypertables AS (
    SELECT COUNT(*)::INT AS hypertable_count
    FROM timescaledb_information.hypertables
    WHERE hypertable_schema = 'public'
      AND hypertable_name IN (
          'ellanlab_revenue_recognition',
          'financial_kpi_daily',
          'ellanlab_monthly_pnl'
      )
),
jobs AS (
    SELECT COUNT(*)::INT AS policy_count
    FROM timescaledb_information.jobs
    WHERE hypertable_schema = 'public'
      AND hypertable_name IN (
          'ellanlab_revenue_recognition',
          'financial_kpi_daily',
          'ellanlab_monthly_pnl'
      )
      AND proc_name IN ('policy_compression', 'policy_retention')
),
dedupe_idx AS (
    SELECT COUNT(*)::INT AS dedupe_index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname IN ('ux_err_dedupe_key_time', 'ux_fkd_dedupe_key_time')
)
SELECT
    ext.ext_ok,
    hypertables.hypertable_count,
    jobs.policy_count,
    dedupe_idx.dedupe_index_count,
    CASE
        WHEN ext.ext_ok
         AND hypertables.hypertable_count = 3
         AND jobs.policy_count = 6
         AND dedupe_idx.dedupe_index_count = 2
        THEN 'SMOKE_OK'
        ELSE 'SMOKE_FAIL'
    END AS smoke_result
FROM ext, hypertables, jobs, dedupe_idx;

\echo '== Hypertables =='
SELECT hypertable_schema, hypertable_name
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public'
  AND hypertable_name IN (
      'ellanlab_revenue_recognition',
      'financial_kpi_daily',
      'ellanlab_monthly_pnl'
  )
ORDER BY hypertable_name;

\echo '== Policies / Jobs =='
SELECT hypertable_name, proc_name, schedule_interval
FROM timescaledb_information.jobs
WHERE hypertable_schema = 'public'
  AND hypertable_name IN (
      'ellanlab_revenue_recognition',
      'financial_kpi_daily',
      'ellanlab_monthly_pnl'
  )
ORDER BY hypertable_name, proc_name;

\echo '== FA-5 Timescale smoke: end =='
