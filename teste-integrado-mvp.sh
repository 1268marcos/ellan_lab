#!/usr/bin/env bash
set -euo pipefail

RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"
LIFECYCLE_BASE_URL="${LIFECYCLE_BASE_URL:-http://localhost:8010}"
ORDER_PICKUP_BASE_URL="${ORDER_PICKUP_BASE_URL:-http://localhost:8003}"

LOCKER_ID="${LOCKER_ID:-SP-ALPHAVILLE-SHOP-LK-001}"
ORDER_ID="${ORDER_ID:-ORD-123}"

echo "=== Subindo serviços Docker ==="
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f 02_docker/docker-compose.yml up -d
else
  docker compose -f 02_docker/docker-compose.yml up -d
fi

echo "=== App Campo: checklist ==="
curl -fsS -X POST "${RUNTIME_BASE_URL}/api/v1/field/checklist" \
  -H "Content-Type: application/json" \
  -d "{\"locker_id\":\"${LOCKER_ID}\",\"task\":\"install\",\"status\":\"pending\"}" \
  | python3 -m json.tool

sleep 2

echo "=== App Campo: status real do locker ==="
curl -fsS "${RUNTIME_BASE_URL}/api/v1/field/locker/${LOCKER_ID}/status" \
  | python3 -m json.tool

echo "=== NOC: dashboard real lifecycle ==="
curl -fsS "${LIFECYCLE_BASE_URL}/api/v1/noc/dashboard" \
  | python3 -m json.tool

echo "=== Suporte: timeline real ==="
support_status="$(
  curl -sS -o /tmp/suporte_timeline_integrado.json -w "%{http_code}" \
    "${ORDER_PICKUP_BASE_URL}/api/v1/support/order/${ORDER_ID}"
)"

python3 -m json.tool /tmp/suporte_timeline_integrado.json

if [ "${support_status}" = "404" ]; then
  echo "SUPORTE_TIMELINE_ORDER_NOT_FOUND: endpoint respondeu contrato 404 para ORDER_ID=${ORDER_ID}."
  echo "Para validar timeline completa, rode com ORDER_ID=<pedido existente>."
elif [ "${support_status}" != "200" ]; then
  echo "SUPORTE_TIMELINE_FAILED: HTTP ${support_status}" >&2
  exit 1
fi

echo "=== Teste integrado MVP finalizado ==="
