-- Orquestrador psql: executa todas as fases em ordem (equivalente a run_rebuild.sh).
-- Uso no container:
--   psql -U admin -d locker_central -v ON_ERROR_STOP=1 -f /path/00_run_all.sql

\echo '=== 00 preamble ==='
\ir 00_preamble.sql
\echo '=== 01 extensions ==='
\ir 01_extensions_schemas.sql
\echo '=== 02 types ==='
\ir 02_types.sql
\echo '=== 03 tables ==='
\ir 03_tables.sql
\echo '=== 03b column patches ==='
\ir 03b_column_patches.sql
\echo '=== 04 sequences ==='
\ir 04_sequences_owned_by.sql
\echo '=== 04b defaults ==='
\ir 04b_column_defaults.sql
\echo '=== 05 functions ==='
\ir 05_functions.sql
\echo '=== 06 constraints ==='
\ir 06_constraints_pk_unique_check.sql
\echo '=== 07 indexes ==='
\ir 07_indexes.sql
\echo '=== 08 foreign keys ==='
\ir 08_foreign_keys.sql
\echo '=== 13 timescaledb ==='
\ir 13_timescaledb_hypertables.sql
\echo '=== 09 views ==='
\ir 09_views.sql
\echo '=== 10 triggers ==='
\ir 10_triggers.sql
\echo '=== 11 rls ==='
\ir 11_rls_policies.sql
\echo '=== 12 comments ==='
\ir 12_comments_misc.sql
\echo '=== 14 schema_migrations seed (order_pickup) ==='
\ir 14_seed_schema_migrations.sql
\echo '=== DONE ==='
