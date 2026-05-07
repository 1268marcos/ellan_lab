#!/usr/bin/env bash
# Smoke manual: pickup em :8002 com API key COO/OPS (mesmo contrato do backend).
# Uso: COO_API_KEY=... ./scripts/coo_widgets_smoke.sh
set -euo pipefail
BASE="${ORDER_PICKUP_URL:-http://localhost:8002}"
KEY="${COO_API_KEY:?defina COO_API_KEY (parceiro COO/OPS ou chave de teste)}"
curl -fsS -H "X-API-Key: ${KEY}" "${BASE}/api/v1/coo/widgets/summary"
echo
