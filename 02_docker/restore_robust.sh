#!/bin/bash
# restore_robust.sh

DB="locker_central"
USER="admin"
PASSWORD="admin123"
HOST="localhost"
PORT="5435"

echo "=== Restauração Robusta ==="

# chmod +x restore_robust.sh - dar permissão de execução

# Executar restauração
# ./restore_robust.sh

# Aguardar e verificar
# sleep 10

# 1. Criar estrutura básica
echo "1. Criando extensões e schemas..."
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d postgres << EOF
DROP DATABASE IF EXISTS $DB;
CREATE DATABASE $DB;
\c $DB
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE SCHEMA IF NOT EXISTS analytics_analytics;
CREATE SCHEMA IF NOT EXISTS topology;
EOF

# 2. Extrair e executar apenas CREATE TABLE (ignorar FKs por enquanto)
echo "2. Criando tabelas sem constraints..."
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DB << 'EOF'
BEGIN;
SET session_replication_role = replica;
DO $$
DECLARE
    sql_line text;
BEGIN
    FOR sql_line IN 
        SELECT line FROM (
            SELECT unnest(string_to_array(pg_read_file('/tmp/schema.sql'), ';')) as line
        ) t
        WHERE line ~ 'CREATE TABLE'
    LOOP
        BEGIN
            EXECUTE sql_line;
        EXCEPTION WHEN duplicate_table THEN
            -- Ignorar
        END;
    END LOOP;
END $$;
COMMIT;
EOF

# 3. Adicionar constraints e índices depois
echo "3. Adicionando constraints..."
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DB << 'EOF'
BEGIN;
DO $$
DECLARE
    sql_line text;
BEGIN
    FOR sql_line IN 
        SELECT line FROM (
            SELECT unnest(string_to_array(pg_read_file('/tmp/schema.sql'), ';')) as line
        ) t
        WHERE line ~ 'ALTER TABLE.*ADD CONSTRAINT'
    LOOP
        BEGIN
            EXECUTE sql_line;
        EXCEPTION WHEN others THEN
            RAISE NOTICE 'Falha ao executar: %', sql_line;
        END;
    END LOOP;
END $$;
COMMIT;
SET session_replication_role = DEFAULT;
EOF

echo "=== Restauração concluída ==="

