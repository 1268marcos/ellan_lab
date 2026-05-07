#!/usr/bin/env bash
# Smoke E2E do portal COO (API order_pickup_service).
# Pré-requisitos: serviço em pé (ex.: compose na porta 8002), jq instalado,
# credencial COO (API key de parceiro COO/OPS ou token de sessão com role).
#
# Uso:
#   COO_API_KEY=... ./07_tests/e2e_coo_smoke.sh
#   COO_BEARER_TOKEN=... ORDER_PICKUP_URL=http://127.0.0.1:8402 ./07_tests/e2e_coo_smoke.sh
set -euo pipefail

echo "=== COO Portal Smoke Tests ==="

if ! command -v jq >/dev/null 2>&1; then
  echo "Erro: jq é necessário (ex.: apt install jq / brew install jq)." >&2
  exit 1
fi

BASE_URL="${ORDER_PICKUP_URL:-http://localhost:8002}"
API_URL="${BASE_URL}/api/v1/coo"

CURL_AUTH=()
if [[ -n "${COO_API_KEY:-}" ]]; then
  CURL_AUTH=(-H "X-API-Key: ${COO_API_KEY}")
elif [[ -n "${COO_BEARER_TOKEN:-}" ]]; then
  CURL_AUTH=(-H "Authorization: Bearer ${COO_BEARER_TOKEN}")
else
  echo "Defina COO_API_KEY (recomendado) ou COO_BEARER_TOKEN (sessão coo/ceo/ops)." >&2
  echo "Ex.: export COO_API_KEY=...   # parceiro com code/tier COO/OPS (ver require_coo_access)" >&2
  exit 1
fi

_coo_get() {
  local path="$1"
  shift
  curl -fsS "${CURL_AUTH[@]}" "$@" "${API_URL}${path}"
}

echo "0. Testing meta..."
_coo_get "/meta" | jq '.'
echo "✅ Meta OK"

echo "1. Testing Widgets Summary..."
_coo_get "/widgets/summary" | jq '.'
echo "✅ Widgets summary OK"

echo "2. Testing Consolidated Dashboard..."
_coo_get "/dashboard/consolidated?days=7" | jq '.'
echo "✅ Dashboard OK"

echo "3. Testing Pickup Health..."
_coo_get "/health/pickups" | jq '.'
echo "✅ Pickup health OK"

echo "4. Testing Active Manifests..."
_coo_get "/logistics/manifests/active" | jq '.'
echo "✅ Manifests OK"

echo "5. Testing SLA by Supplier..."
_coo_get "/suppliers/sla" | jq '.'
echo "✅ SLA OK"

echo "6. Testing Network Uptime..."
_coo_get "/kpis/network/uptime?days=30" | jq '.'
echo "✅ Uptime OK"

echo "7. Testing Pending Approvals..."
_coo_get "/approvals/pending" | jq '.'
echo "✅ Approvals OK"

echo "=== All COO portal smoke tests passed! ==="
