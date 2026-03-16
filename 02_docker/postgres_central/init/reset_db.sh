#!/bin/bash

# Nome do container (ajuste conforme seu docker-compose)
CONTAINER_NAME="postgres_central"
DB_USER="admin"
DB_NAME="locker_central"  # ou o nome do seu banco

echo "Resetando banco de dados..."

# Executar comandos SQL dentro do container
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME << EOF
-- Desabilitar triggers
SET session_replication_role = 'replica';

-- Truncar tabelas
TRUNCATE TABLE credits CASCADE;
TRUNCATE TABLE pickup_attempts CASCADE;
TRUNCATE TABLE pickup_tokens CASCADE;
TRUNCATE TABLE payments CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE gateway_events CASCADE;

-- Reabilitar triggers
SET session_replication_role = 'origin';

-- Verificar resultado Verificar se todas estão vazias

EOF

echo "Banco resetado com sucesso!"