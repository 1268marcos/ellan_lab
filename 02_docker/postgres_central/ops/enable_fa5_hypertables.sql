-- enable_fa5_hypertables.sql
-- Converte tabelas FA-5 para hypertables em DB já existente.
-- Requer: CREATE EXTENSION timescaledb já aplicado.
--
-- Atenção:
-- Timescale exige que índices únicos/PK incluam a coluna de partição temporal.
-- Por isso este script ajusta PKs para modelo composto (time + id).

BEGIN;

-- financial_kpi_daily
ALTER TABLE IF EXISTS financial_kpi_daily
    DROP CONSTRAINT IF EXISTS financial_kpi_daily_pkey;
ALTER TABLE IF EXISTS financial_kpi_daily
    ADD CONSTRAINT financial_kpi_daily_pkey PRIMARY KEY (snapshot_date, id);

-- ellanlab_revenue_recognition
ALTER TABLE IF EXISTS ellanlab_revenue_recognition
    DROP CONSTRAINT IF EXISTS ellanlab_revenue_recognition_pkey;
ALTER TABLE IF EXISTS ellanlab_revenue_recognition
    ADD CONSTRAINT ellanlab_revenue_recognition_pkey PRIMARY KEY (recognition_date, id);

-- ellanlab_monthly_pnl
ALTER TABLE IF EXISTS ellanlab_monthly_pnl
    DROP CONSTRAINT IF EXISTS ellanlab_monthly_pnl_pkey;
ALTER TABLE IF EXISTS ellanlab_monthly_pnl
    ADD CONSTRAINT ellanlab_monthly_pnl_pkey PRIMARY KEY (pnl_month, id);

COMMIT;

SELECT create_hypertable('ellanlab_revenue_recognition', 'recognition_date', if_not_exists => TRUE, migrate_data => TRUE);
SELECT create_hypertable('financial_kpi_daily', 'snapshot_date', if_not_exists => TRUE, migrate_data => TRUE);
SELECT create_hypertable('ellanlab_monthly_pnl', 'pnl_month', if_not_exists => TRUE, migrate_data => TRUE);

ALTER TABLE ellanlab_revenue_recognition SET (timescaledb.compress = true);
ALTER TABLE financial_kpi_daily SET (timescaledb.compress = true);
ALTER TABLE ellanlab_monthly_pnl SET (timescaledb.compress = true);

SELECT add_compression_policy('ellanlab_revenue_recognition', INTERVAL '14 days', if_not_exists => TRUE);
SELECT add_compression_policy('financial_kpi_daily', INTERVAL '14 days', if_not_exists => TRUE);
SELECT add_compression_policy('ellanlab_monthly_pnl', INTERVAL '90 days', if_not_exists => TRUE);

SELECT add_retention_policy('ellanlab_revenue_recognition', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('financial_kpi_daily', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('ellanlab_monthly_pnl', INTERVAL '5 years', if_not_exists => TRUE);
