#!/bin/bash
# cleanup-and-rebuild.sh - Limpa e reconstrói com Dockerfile custom

set -e

echo "🗑️  Parando todos os containers..."
docker compose down

echo "🗑️  Removendo volume antigo do PostgreSQL..."
# Remove volumes específicos
docker volume rm 02_docker_postgres_central_data 2>/dev/null || \
docker volume ls -q | grep postgres_central | xargs -r docker volume rm

echo "🗑️  Removendo dados antigos do diretório..."
sudo rm -rf ../03_data/postgres_central
echo "✅ Dados antigos removidos"

echo "🔨  Construindo nova imagem com TimescaleDB..."
docker compose build --no-cache postgres_central

echo "🚀  Subindo apenas o PostgreSQL para teste..."
docker compose up -d postgres_central

echo "⏳  Aguardando PostgreSQL inicializar (45 segundos)..."
sleep 45

echo "📊  Verificando logs do PostgreSQL..."
docker compose logs postgres_central --tail=30

echo ""
echo "📋  Verificando extensões instaladas..."
docker exec postgres_central psql -U admin -d locker_central -c "SELECT extname, extversion FROM pg_extension ORDER BY extname;" 2>/dev/null || \
    echo "⚠️  Ainda inicializando, aguarde mais..."

echo ""
echo "🔍  Verificando shared_preload_libraries..."
docker exec postgres_central psql -U admin -d locker_central -c "SHOW shared_preload_libraries;" 2>/dev/null || \
    echo "⏳  PostgreSQL ainda iniciando..."

echo ""
read -p "❓ O PostgreSQL está saudável? (veja os logs acima) [s/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "🚀  Subindo todos os containers..."
    docker compose up -d
    echo ""
    echo "✅  Ambiente reconstruído com sucesso!"
    echo "📝  Verifique os logs com: docker compose logs -f"
else
    echo "❌  Problemas na inicialização. Verifique os logs:"
    echo "   docker compose logs postgres_central"
    exit 1
fi