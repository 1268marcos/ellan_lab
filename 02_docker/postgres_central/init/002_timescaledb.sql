-- 002_timescaledb.sql
-- Executado no bootstrap do banco (somente em volume novo).
-- Garante que a extensão TimescaleDB fique ativa no DB inicial.

CREATE EXTENSION IF NOT EXISTS timescaledb;

DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB version: %', (
        SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'
    );
END $$;
