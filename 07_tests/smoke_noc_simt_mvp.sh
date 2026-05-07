#!/usr/bin/env bash
set -euo pipefail

RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"
LIFECYCLE_BASE_URL="${LIFECYCLE_BASE_URL:-http://localhost:8010}"
INCIDENT_ID="${INCIDENT_ID:-INC-MVP-001}"

echo "=== Smoke: NOC/SIMT MVP ==="
echo "RUNTIME_BASE_URL=${RUNTIME_BASE_URL}"
echo "LIFECYCLE_BASE_URL=${LIFECYCLE_BASE_URL}"

curl -fsS "${RUNTIME_BASE_URL}/api/v1/noc/health" | python3 -m json.tool >/tmp/noc_runtime_health.json
curl -fsS "${RUNTIME_BASE_URL}/api/v1/noc/simt/summary" | python3 -m json.tool >/tmp/noc_simt_summary.json
curl -fsS -X POST "${RUNTIME_BASE_URL}/api/v1/noc/incidents/ack" \
  -H "Content-Type: application/json" \
  -d "{\"incident_id\":\"${INCIDENT_ID}\",\"acknowledged_by\":\"noc_operator\"}" \
  | python3 -m json.tool >/tmp/noc_runtime_ack.json

curl -fsS "${LIFECYCLE_BASE_URL}/api/v1/noc/health" | python3 -m json.tool >/tmp/noc_lifecycle_health.json
curl -fsS "${LIFECYCLE_BASE_URL}/api/v1/noc/dashboard" | python3 -m json.tool >/tmp/noc_lifecycle_dashboard.json

python3 - <<'PY'
import json
from pathlib import Path

runtime_health = json.loads(Path("/tmp/noc_runtime_health.json").read_text())
summary = json.loads(Path("/tmp/noc_simt_summary.json").read_text())
runtime_ack = json.loads(Path("/tmp/noc_runtime_ack.json").read_text())
lifecycle_health = json.loads(Path("/tmp/noc_lifecycle_health.json").read_text())
dashboard = json.loads(Path("/tmp/noc_lifecycle_dashboard.json").read_text())

assert runtime_health["status"] == "ok"
assert summary["status"] == "ok"
assert runtime_ack["status"] == "acknowledged"
assert lifecycle_health["status"] == "ok"
assert "lockers_total" in dashboard
print("NOC_SIMT_SMOKE_OK")
PY
