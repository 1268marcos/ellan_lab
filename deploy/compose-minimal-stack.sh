#!/usr/bin/env bash
# Sobe apenas a cadeia necessária para fluxo de pagamento online + confirmação interna + runtime + lifecycle.
# Pré-requisito: ficheiro 02_docker/.env com ORDER_INTERNAL_TOKEN, segredos do gateway, etc. (igual ao compose completo).
#
# Uso (a partir da raiz do repositório):
#   ./deploy/compose-minimal-stack.sh
#
# Serviços excluídos (exemplos): billing_fiscal_*, workers fiscais, Grafana/Metabase, simulador —
# acrescente-os se precisar de emissão fiscal ou observabilidade.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}/02_docker"

SERVICES=(
  postgres_central
  redis_central
  mqtt
  backend_runtime
  order_lifecycle_service
  order_lifecycle_worker
  payment_gateway
  order_pickup_service
)

docker compose -f docker-compose.yml up -d --build "${SERVICES[@]}"

echo ""
echo "Stack mínima em execução. Health (host):"
echo "  runtime   http://localhost:8200/health"
echo "  gateway   http://localhost:8000/health"
echo "  lifecycle http://localhost:8010/health  (se exposto)"
echo "  pickup    http://localhost:8003/docs (ou rota interna com token)"
echo ""
echo "Para encerrar: docker compose -f docker-compose.yml down"
