#!/bin/bash

echo "=== Iniciando restauração do banco de dados ==="

# chmod +x restore_db.sh - dar permissão de execução

# Executar restauração
# ./restore_db.sh

# Aguardar e verificar
# sleep 10

# Aguardar PostgreSQL ficar pronto
echo "Aguardando PostgreSQL ficar saudável..."
until docker exec postgres_central pg_isready -U admin; do
  sleep 2
done

echo "PostgreSQL está pronto!"

# Copiar o schema para o container
echo "Copiando schema para o container..."
docker cp complete_schema_20260517_e.sql postgres_central:/tmp/schema.sql

# Executar a restauração em etapas
echo "Restaurando schema (etapa 1 - estrutura básica)..."
docker exec postgres_central psql -U admin -d locker_central -v ON_ERROR_STOP=0 << 'EOF'
-- Desabilitar triggers e constraints temporariamente
SET session_replication_role = replica;
SET client_min_messages = warning;

-- Criar tipos primeiro (eles não dependem de nada)
DO $$
DECLARE
    sql_line text;
BEGIN
    -- Extrair e executar apenas CREATE TYPE statements
    FOR sql_line IN 
        SELECT line FROM (
            SELECT unnest(string_to_array(pg_read_file('/tmp/schema.sql'), ';')) as line
        ) t
        WHERE line ~ '^CREATE TYPE'
    LOOP
        BEGIN
            EXECUTE sql_line;
        EXCEPTION WHEN duplicate_object THEN
            RAISE NOTICE 'Type already exists, skipping: %', sql_line;
        END;
    END LOOP;
END $$;

-- Criar extensões
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Criar schemas
CREATE SCHEMA IF NOT EXISTS analytics_analytics;
CREATE SCHEMA IF NOT EXISTS topology;

EOF

echo "Etapa 1 concluída."

# Restaurar o restante com tratamento de erros
echo "Restaurando tabelas e constraints..."
docker exec postgres_central psql -U admin -d locker_central -v ON_ERROR_STOP=0 -f /tmp/schema.sql 2>&1 | grep -v "already exists" | grep -v "duplicate key" || true

# Reativar triggers
docker exec postgres_central psql -U admin -d locker_central -c "SET session_replication_role = DEFAULT;"

echo "=== Restauração concluída ==="