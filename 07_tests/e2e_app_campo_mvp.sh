#!/bin/bash
set -e

RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"
LOCKER_ID="${LOCKER_ID:-SP-ALPHAVILLE-SHOP-LK-001}"

echo "=== E2E App Campo MVP ==="
echo "RUNTIME_BASE_URL=${RUNTIME_BASE_URL}"
echo "LOCKER_ID=${LOCKER_ID}"

# Criar checklist
curl -fsS -X POST "${RUNTIME_BASE_URL}/api/v1/field/checklist" \
  -d "{\"locker_id\":\"${LOCKER_ID}\",\"task\":\"install\",\"status\":\"pending\"}" \
  -H "Content-Type: application/json"

echo

# Verificar status real do locker
curl -fsS "${RUNTIME_BASE_URL}/api/v1/field/locker/${LOCKER_ID}/status" | grep "operational"

echo "E2E App Campo PASS"
