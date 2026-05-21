#!/bin/bash
# restore_full_schema.sh

# chmod +x restore_full_schema.sh - dar permissão de execução

# Executar restauração
# ./restore_full_schema.sh

# Aguardar e verificar
# sleep 10


echo "=== INICIANDO RESTAURAÇÃO COMPLETA DO SCHEMA ==="

# 1. Parar todos os serviços
echo "1. Parando todos os containers..."
docker compose down -v

# 2. Remover dados antigos completamente
echo "2. Removendo dados antigos..."
sudo rm -rf ../03_data/postgres_central
sudo rm -rf ../03_data/sqlite

# 3. Criar diretório de inicialização
echo "3. Preparando scripts de inicialização..."
mkdir -p ./postgres_central/init

# 4. Criar script de init para garantir extensões
cat > ./postgres_central/init/00-init-extensions.sql << 'EOF'
-- Script executado na primeira inicialização do banco
\c locker_central

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Configurar pg_cron
ALTER SYSTEM SET cron.database_name = 'locker_central';
SELECT pg_reload_conf();

-- Criar schemas adicionais
CREATE SCHEMA IF NOT EXISTS analytics_analytics;
CREATE SCHEMA IF NOT EXISTS topology;

-- Log
DO $$ BEGIN RAISE NOTICE '✅ Extensões e schemas criados em %', NOW(); END $$;
EOF

# 5. Iniciar apenas o PostgreSQL
echo "5. Iniciando PostgreSQL..."
docker compose up -d postgres_central

# 6. Aguardar PostgreSQL ficar saudável
echo "6. Aguardando PostgreSQL ficar pronto..."
sleep 30

# Verificar se está saudável
for i in {1..30}; do
    if docker exec postgres_central pg_isready -U admin &>/dev/null; then
        echo "✅ PostgreSQL está pronto!"
        break
    fi
    echo "Aguardando PostgreSQL... ($i/30)"
    sleep 2
done

# 7. Copiar e executar o schema completo
echo "7. Executando schema completo..."
docker cp complete_schema_20260517_e.sql postgres_central:/tmp/schema.sql

# Executar o schema com tratamento de erros
docker exec -i postgres_central psql -U admin -d locker_central << 'EOF'
-- Desabilitar verificações temporariamente para importação
SET session_replication_role = replica;
SET client_min_messages = warning;

-- Executar o schema completo
\i /tmp/schema.sql

-- Reabilitar verificações
SET session_replication_role = DEFAULT;
SET client_min_messages = default;

-- Verificar se as principais tabelas foram criadas
DO $$
DECLARE
    tables text[] := ARRAY['orders', 'order_items', 'allocations', 'pickups', 'pickup_tokens', 
                           'payment_transactions', 'invoices', 'fiscal_documents', 'users', 'lockers'];
    t text;
BEGIN
    FOREACH t IN ARRAY tables
    LOOP
        IF EXISTS (SELECT FROM pg_tables WHERE tablename = t) THEN
            RAISE NOTICE '✅ Tabela % existe', t;
        ELSE
            RAISE WARNING '❌ Tabela % NÃO existe', t;
        END IF;
    END LOOP;
END $$;

-- Verificar extensões
SELECT extname, extversion FROM pg_extension ORDER BY extname;
EOF

echo ""
echo "8. Verificando estrutura da tabela orders..."
docker exec postgres_central psql -U admin -d locker_central -c "\d orders" | head -50

echo ""
echo "9. Verificando total de tabelas..."
docker exec postgres_central psql -U admin -d locker_central -c "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';"

# 10. Iniciar todos os serviços
echo ""
echo "10. Iniciando todos os serviços..."
docker compose up -d

echo ""
echo "=== RESTAURAÇÃO CONCLUÍDA ==="
echo "Aguardando 30 segundos para os serviços iniciarem..."
sleep 30

# 11. Verificar status
echo ""
echo "=== STATUS DOS SERVIÇOS ==="
docker compose ps

echo ""
echo "=== VERIFICANDO LOGS DO ORDER_PICKUP_SERVICE ==="
docker compose logs order_pickup_service --tail=20

echo ""
echo "=== VERIFICANDO LOGS DO PARTNER_WEBHOOK_DELIVERY_WORKER ==="
docker compose logs partner_webhook_delivery_worker --tail=20