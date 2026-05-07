#!/usr/bin/env bash
set -euo pipefail

RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"
LOCKER_ID="${LOCKER_ID:-SP-ALPHAVILLE-SHOP-LK-001}"

echo "=== Smoke: App Campo MVP ==="
echo "RUNTIME_BASE_URL=${RUNTIME_BASE_URL}"

curl -fsS "${RUNTIME_BASE_URL}/api/v1/field/health" | python3 -m json.tool >/tmp/app_campo_health.json

curl -fsS -X POST "${RUNTIME_BASE_URL}/api/v1/field/checklist" \
  -H "Content-Type: application/json" \
  -d "{\"locker_id\":\"${LOCKER_ID}\",\"task\":\"check_power\",\"status\":\"completed\"}" \
  | python3 -m json.tool >/tmp/app_campo_checklist.json

curl -fsS "${RUNTIME_BASE_URL}/api/v1/field/locker/${LOCKER_ID}/status" \
  | python3 -m json.tool >/tmp/app_campo_locker_status.json

python3 - <<'PY'
import json
from pathlib import Path

health = json.loads(Path("/tmp/app_campo_health.json").read_text())
checklist = json.loads(Path("/tmp/app_campo_checklist.json").read_text())
locker = json.loads(Path("/tmp/app_campo_locker_status.json").read_text())

assert health["status"] == "ok"
assert checklist["status"] == "accepted"
assert locker["status"] == "operational"
print("APP_CAMPO_SMOKE_OK")
PY
