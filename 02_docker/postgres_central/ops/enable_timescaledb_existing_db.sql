-- enable_timescaledb_existing_db.sql
-- Uso: ambiente já em execução com volume existente (init scripts não reexecutam).
-- Execute manualmente no postgres_central:
--   psql -U admin -d locker_central -f /path/enable_timescaledb_existing_db.sql

CREATE EXTENSION IF NOT EXISTS timescaledb;

SELECT extname, extversion
FROM pg_extension
WHERE extname = 'timescaledb';
