#!/bin/bash
# verify-extensions.sh

echo "🔍 Verificando extensões no PostgreSQL..."

# Aguarda PostgreSQL ficar pronto
until docker exec postgres_central pg_isready -h 127.0.0.1 -p 5432 -U admin -d locker_central > /dev/null 2>&1; do
    echo "⏳ Aguardando PostgreSQL ficar pronto..."
    sleep 2
done

echo "✅ PostgreSQL está pronto!"
echo ""

# Lista extensões
docker exec postgres_central psql -U admin -d locker_central << EOF
\x on
SELECT 
    extname AS "Extension Name",
    extversion AS "Version"
FROM pg_extension 
WHERE extname IN ('timescaledb', 'postgis', 'pg_cron', 'uuid-ossp', 'hstore')
ORDER BY extname;

\dx timescaledb
\dx postgis

SELECT '✅ TimescaleDB version: ' || extversion FROM pg_extension WHERE extname = 'timescaledb';
SELECT '✅ PostGIS version: ' || postgis_version();

SHOW shared_preload_libraries;
EOF

echo ""
echo "✅ Verificação concluída"